"""Software preview of how the AK is oriented in every item context.

NOT the game: this is a re-implementation (numpy + PIL) of the relevant parts of the Minecraft 1.20.1 item rendering
chain, applied to the REAL generated model (assets/donbass/models/item/ak_rifle.json), so a wrong sign or axis in the
model / display transforms shows up as a visibly wrong picture. The chain (all matrices applied left to right):

  first person   : camera -> hand offset (AkClientExtensions / ItemInHandRenderer.applyItemArmTransform)
                   -> ItemTransform(display) -> translate(-0.5)
  third person   : entity model space -> ModelPart.translateAndRotate(arm: pivot, then Rz.Ry.Rx)
                   -> Rx(-90) -> Ry(180) -> translate(+-1/16, 0.125, -0.625)   (ItemInHandLayer)
                   -> ItemTransform(display) -> translate(-0.5)
  ItemTransform  : translate(+-t) . Rx(rx).Ry(ry).Rz(rz) . scale        (JOML rotationXYZ; left hand: x of t, ry, rz negated)
  gui / ground / fixed: ItemTransform only

Entity model space: +x = the model's left, +y = down, +z = backward (the model looks to -z).
Usage:  python3 tools/preview_ak.py [out.png]     (needs numpy and Pillow; not used by the build or the CI)
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "..", "src", "main", "resources", "assets", "donbass")
MODEL = os.path.join(ASSETS, "models", "item", "ak_rifle.json")
TEXTURE = os.path.join(ASSETS, "textures", "item", "ak_rifle_model.png")


# ------------------------------------------------------------------ matrices ----
def T(x, y, z):
    m = np.eye(4)
    m[:3, 3] = (x, y, z)
    return m


def S(x, y, z):
    return np.diag([x, y, z, 1.0])


def Rx(a):
    c, s = math.cos(a), math.sin(a)
    m = np.eye(4)
    m[1, 1], m[1, 2], m[2, 1], m[2, 2] = c, -s, s, c
    return m


def Ry(a):
    c, s = math.cos(a), math.sin(a)
    m = np.eye(4)
    m[0, 0], m[0, 2], m[2, 0], m[2, 2] = c, s, -s, c
    return m


def Rz(a):
    c, s = math.cos(a), math.sin(a)
    m = np.eye(4)
    m[0, 0], m[0, 1], m[1, 0], m[1, 1] = c, -s, s, c
    return m


def deg(a):
    return a * math.pi / 180.0


def item_transform(display, left):
    """ItemTransform.apply(leftHand, poseStack)."""
    rx, ry, rz = display["rotation"]
    tx, ty, tz = display["translation"]
    sx, sy, sz = display["scale"]
    if left:
        ry, rz, tx = -ry, -rz, -tx
    # JOML Quaternionf.rotationXYZ(x, y, z) == Rx * Ry * Rz as a matrix
    return T(tx / 16, ty / 16, tz / 16) @ Rx(deg(rx)) @ Ry(deg(ry)) @ Rz(deg(rz)) @ S(sx, sy, sz) @ T(-.5, -.5, -.5)


def model_part(pivot, rx, ry, rz):
    """ModelPart.translateAndRotate: translate(pivot/16), rotationZYX(z, y, x) == Rz * Ry * Rx."""
    return T(pivot[0] / 16, pivot[1] / 16, pivot[2] / 16) @ Rz(rz) @ Ry(ry) @ Rx(rx)


# ------------------------------------------------------------------- geometry ----
def box_polys(f, t, color, rot=None, only=None):
    """Polygons (4 corners in the box's own space, normal, colour) of a cuboid; f, t in blocks."""
    corners = np.array([[(t[0] if i & 4 else f[0]), (t[1] if i & 2 else f[1]), (t[2] if i & 1 else f[2])]
                        for i in range(8)], dtype=float)
    rotm = np.eye(3)
    if rot:
        o = np.array(rot["origin"], dtype=float) / 16
        a = deg(rot["angle"])
        rotm = {"x": Rx, "y": Ry, "z": Rz}[rot["axis"]](a)[:3, :3]
        corners = (corners - o) @ rotm.T + o
    idx = {  # corner index = 4*xbit + 2*ybit + zbit
        "north": (0, 2, 6, 4), "south": (1, 5, 7, 3),
        "west": (0, 1, 3, 2), "east": (4, 6, 7, 5),
        "down": (0, 4, 5, 1), "up": (2, 3, 7, 6),
    }
    normals = {"north": (0, 0, -1), "south": (0, 0, 1), "west": (-1, 0, 0), "east": (1, 0, 0),
               "down": (0, -1, 0), "up": (0, 1, 0)}
    out = []
    for face, ci in idx.items():
        out.append((corners[list(ci)], rotm @ np.array(normals[face], dtype=float), color))
    return out


def model_polys(texture):
    """All polygons of the rifle model, in model space (blocks), with the colour of the face's swatch."""
    d = json.load(open(MODEL))
    tex = Image.open(texture).convert("RGB") if os.path.exists(texture) else None
    polys = []
    for el in d["elements"]:
        uv = el["faces"]["north"]["uv"]
        cx, cy = int((uv[0] + uv[2]) / 2), int((uv[1] + uv[3]) / 2)
        color = tex.getpixel((cx, cy)) if tex else (120, 120, 120)
        f = [v / 16 for v in el["from"]]
        t = [v / 16 for v in el["to"]]
        polys += box_polys(f, t, color, el.get("rotation"))
    return polys, d["display"]


def transform_polys(polys, m):
    out = []
    for corners, normal, color in polys:
        h = np.c_[corners, np.ones(len(corners))] @ m.T
        out.append((h[:, :3], m[:3, :3] @ normal / max(1e-9, np.linalg.norm(m[:3, :3] @ normal)), color))
    return out


# ------------------------------------------------------------------ rasteriser ----
class View:
    """Maps world points to (screen x, screen y, nearness) and back-face / lighting information."""

    def __init__(self, project, light=(-0.4, 0.7, 0.6)):
        self.project = project
        self.light = np.array(light) / np.linalg.norm(light)


def draw(polys, view, size, scale, centre, bg=(34, 38, 46)):
    """Z-buffered flat-shaded rendering. view.project(points) -> (sx, sy, near, nview) with sx right, sy up."""
    w, h = size
    img = np.zeros((h, w, 3), dtype=float)
    img[:] = bg
    zbuf = np.full((h, w), -1e9)
    for corners, normal, color in polys:
        sx, sy, near, nview = view.project(corners, normal)
        if sx is None:
            continue
        px = centre[0] + sx * scale
        py = centre[1] - sy * scale
        shade = 0.45 + 0.55 * max(0.0, abs(float(np.dot(nview, view.light))))
        col = np.array(color, dtype=float) * shade
        for tri in [(0, i, i + 1) for i in range(1, len(px) - 1)]:
            ax, ay, bx, by, cx, cy = px[tri[0]], py[tri[0]], px[tri[1]], py[tri[1]], px[tri[2]], py[tri[2]]
            den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
            if abs(den) < 1e-9:
                continue
            x0, x1 = int(max(0, math.floor(min(ax, bx, cx)))), int(min(w - 1, math.ceil(max(ax, bx, cx))))
            y0, y1 = int(max(0, math.floor(min(ay, by, cy)))), int(min(h - 1, math.ceil(max(ay, by, cy))))
            if x0 > x1 or y0 > y1:
                continue
            xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
            l1 = ((by - cy) * (xs - cx) + (cx - bx) * (ys - cy)) / den
            l2 = ((cy - ay) * (xs - cx) + (ax - cx) * (ys - cy)) / den
            l3 = 1 - l1 - l2
            inside = (l1 >= -1e-4) & (l2 >= -1e-4) & (l3 >= -1e-4)
            z = l1 * near[tri[0]] + l2 * near[tri[1]] + l3 * near[tri[2]]
            sub = zbuf[y0:y1 + 1, x0:x1 + 1]
            mask = inside & (z > sub)
            sub[mask] = z[mask]
            img[y0:y1 + 1, x0:x1 + 1][mask] = col
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))


def ortho(axes):
    """axes: functions of a model-space point -> (screen x, screen y, nearness)."""
    ax, ay, an = axes

    def project(corners, normal):
        sx = np.array([ax(p) for p in corners])
        sy = np.array([ay(p) for p in corners])
        near = np.array([an(p) for p in corners])
        nview = np.array([ax(normal), ay(normal), an(normal)])
        return sx, sy, near, nview
    return project


def persp(fov_deg=70.0, aspect=16 / 9, znear=0.05):
    th = math.tan(deg(fov_deg) / 2)

    def clip(corners):
        pts = [p for p in corners]
        out = []
        for i in range(len(pts)):
            a, b = pts[i], pts[(i + 1) % len(pts)]
            ina, inb = a[2] < -znear, b[2] < -znear
            if ina:
                out.append(a)
            if ina != inb:
                k = (-znear - a[2]) / (b[2] - a[2])
                out.append(a + (b - a) * k)
        return out

    def project(corners, normal):
        pts = clip(corners)
        if len(pts) < 3:
            return None, None, None, None
        p = np.array(pts)
        sx = p[:, 0] / (-p[:, 2] * th)
        sy = p[:, 1] / (-p[:, 2] * th)
        return sx, sy, 1.0 / (-p[:, 2]), normal
    return project


# --------------------------------------------------------------------- scenes ----
def panel(img, title, size):
    out = Image.new("RGB", (size[0], size[1] + 18), (20, 22, 28))
    out.paste(img, (0, 18))
    ImageDraw.Draw(out).text((6, 3), title, fill=(230, 230, 230))
    return out


def player_boxes(arm_angles, head, left_main):
    """Boxes of the humanoid model in model space (blocks) as (corners-polys, colour), arms posed.
    arm_angles: {'right': (x, y, z), 'left': (x, y, z)}; head: (xRot, yRot)."""
    polys = []

    def add(f, t, color, m=None, face_only=None):
        for p in box_polys([v / 16 for v in f], [v / 16 for v in t], color):
            if m is not None:
                h = np.c_[p[0], np.ones(4)] @ m.T
                p = (h[:, :3], m[:3, :3] @ p[1], p[2])
            polys.append(p)

    skin, cloth, dark = (214, 168, 128), (80, 96, 70), (56, 60, 66)
    add((-4, 0, -2), (4, 12, 2), cloth)
    add((-3.9, 12, -2), (0.1, 24, 2), dark)                                     # right leg
    add((-0.1, 12, -2), (3.9, 24, 2), dark)                                     # left leg
    hm = model_part((0, 0, 0), head[0], head[1], 0)
    add((-4, -8, -4), (4, 0, 4), skin, hm)
    add((-4.05, -8.05, -4.4), (4.05, -6.0, -3.9), (70, 50, 30), hm)           # hair band at the front: shows the facing
    rm = model_part((-5, 2, 0), *arm_angles["right"])
    lm = model_part((5, 2, 0), *arm_angles["left"])
    add((-3, -2, -2), (1, 10, 2), cloth, rm)
    add((-1, -2, -2), (3, 10, 2), cloth, lm)
    add((-3, 8, -2), (1, 10, 2), skin, rm)
    add((-1, 8, -2), (3, 10, 2), skin, lm)
    return polys, rm, lm


def crossbow_hold(head, left_handed):
    """AnimationUtils.animateCrossbowHold, both arms."""
    hx, hy = head
    main = (-math.pi / 2 + hx + 0.1, (0.3 if left_handed else -0.3) + hy, 0.0)
    other = (-1.5 + hx, (-0.6 if left_handed else 0.6) + hy, 0.0)
    return {"right": other if left_handed else main, "left": main if left_handed else other}


def third_person(display, polys, left_handed, head, view_name, size=(380, 300)):
    arms = crossbow_hold(head, left_handed)
    body, rm, lm = player_boxes(arms, head, left_handed)
    arm = lm if left_handed else rm
    flag = -1 if left_handed else 1
    layer = arm @ Rx(deg(-90)) @ Ry(deg(180)) @ T(flag / 16, 0.125, -0.625)
    key = "thirdperson_lefthand" if left_handed else "thirdperson_righthand"
    gun = transform_polys(polys, layer @ item_transform(display[key], left_handed))
    views = {
        "right side": ortho((lambda p: -p[2], lambda p: -p[1], lambda p: -p[0])),
        "top": ortho((lambda p: -p[0], lambda p: -p[2], lambda p: -p[1])),
        "back": ortho((lambda p: -p[0], lambda p: -p[1], lambda p: p[2])),
        "front": ortho((lambda p: p[0], lambda p: -p[1], lambda p: -p[2])),
    }
    # nearness must grow towards the viewer; the lambdas above are written as "nearer = larger"
    v = View(views[view_name])
    interest = {"right side": (0.75, -0.45), "top": (0.0, 0.65), "back": (0.0, -0.45), "front": (0.0, -0.45)}[view_name]
    sc = 125.0 if view_name != "top" else 140.0
    centre = (size[0] / 2 - interest[0] * sc, size[1] / 2 + interest[1] * sc)
    img = draw(body + gun, v, size, sc, centre)
    return panel(img, f"3rd person {'LEFT' if left_handed else 'RIGHT'}-handed, head pitch "
                      f"{head[0]:+.2f}: {view_name}", size)


def first_person(display, polys, left, reload_progress=0.0, recoil=0.0, size=(480, 270)):
    side = -1 if left else 1
    key = "firstperson_lefthand" if left else "firstperson_righthand"
    m = T(side * 0.56, -0.52, -0.72)
    m = m @ T(0, recoil * 0.015, recoil * 0.09) @ Rx(deg(recoil * 3.5))
    if reload_progress > 0:
        dip = math.sin(reload_progress * math.pi)
        m = m @ T(0, -0.22 * dip, 0.05 * dip) @ Rx(deg(38 * dip)) @ Rz(deg(side * -14 * dip))
    gun = transform_polys(polys, m @ item_transform(display[key], left))
    img = draw(gun, View(persp()), size, size[1] / 2, (size[0] / 2, size[1] / 2))
    d = ImageDraw.Draw(img)
    d.line((size[0] / 2 - 6, size[1] / 2, size[0] / 2 + 6, size[1] / 2), fill=(255, 255, 255))
    d.line((size[0] / 2, size[1] / 2 - 6, size[0] / 2, size[1] / 2 + 6), fill=(255, 255, 255))
    label = "1st person " + ("LEFT" if left else "RIGHT") + (f" reload {reload_progress:.1f}" if reload_progress else "") \
        + (f" recoil {recoil:.1f}" if recoil else "")
    return panel(img, label, size)


def flat_context(display, polys, name, spin=0.0, viewer="+z", size=(240, 240)):
    m = Ry(deg(spin)) @ item_transform(display[name], False)
    gun = transform_polys(polys, m)
    if viewer == "+z":      # gui: the viewer is at +z, x to the right
        proj = ortho((lambda p: p[0], lambda p: p[1], lambda p: p[2]))
    else:                   # item frame: the viewer is at -z, x to the left
        proj = ortho((lambda p: -p[0], lambda p: p[1], lambda p: -p[2]))
    img = draw(gun, View(proj), size, size[0], (size[0] / 2, size[1] / 2))
    d = ImageDraw.Draw(img)
    d.rectangle((size[0] / 2 - size[0] / 2 + 1, 1, size[0] - 2, size[1] - 2), outline=(90, 90, 100))
    return panel(img, f"{name}" + (f" spin {spin:.0f}" if name == "ground" else "") + f" (viewer {viewer})", size)


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "preview_ak.png")
    polys, display = model_polys(TEXTURE)
    rows = []
    rows.append([first_person(display, polys, False), first_person(display, polys, True)])
    rows.append([first_person(display, polys, False, reload_progress=0.5),
                 first_person(display, polys, False, recoil=1.0)])
    for left in (False, True):
        for head in ((0.0, 0.0),):
            rows.append([third_person(display, polys, left, head, v) for v in ("right side", "top")])
            rows.append([third_person(display, polys, left, head, v) for v in ("back", "front")])
    rows.append([third_person(display, polys, False, (0.5, 0.0), "right side"),
                 third_person(display, polys, False, (-0.5, 0.0), "right side")])
    rows.append([flat_context(display, polys, "gui"), flat_context(display, polys, "fixed", viewer="-z"),
                 flat_context(display, polys, "ground", 0), flat_context(display, polys, "ground", 90)])
    width = max(sum(p.width for p in r) for r in rows)
    height = sum(max(p.height for p in r) for r in rows)
    sheet = Image.new("RGB", (width, height), (10, 10, 12))
    y = 0
    for r in rows:
        x = 0
        for p in r:
            sheet.paste(p, (x, y))
            x += p.width
        y += max(p.height for p in r)
    sheet.save(out)
    print("preview written to", out, sheet.size)


if __name__ == "__main__":
    main()

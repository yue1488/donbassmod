"""Procedural textures for the 0.2.0 gear and mobs (PIL only, deterministic):
item icons (rifle, parts, 16 armour pieces), armour layer sheets (64x32) and entity skins (64x64).

Box-unfolding follows the vanilla UV convention: a w x h x d box at texOffs (u, v) occupies
top (u+d, v, w, d), bottom (u+d+w, v, w, d), right (u, v+d, d, h), front (u+d, v+d, w, h),
left (u+d+w, v+d, d, h), back (u+2d+w, v+d, w, h).
"""
import math
import os
import random
import zlib

from PIL import Image

from gen_textures import ITEM_DIR, ROOT, clamp, rng, shade

ARMOR_DIR = os.path.join(ROOT, "models", "armor")
ENTITY_DIR = os.path.join(ROOT, "entity")


def rgba(c, a=255):
    return (c[0], c[1], c[2], a) if len(c) == 3 else c


# ------------------------------------------------------------------ noise ----
def vnoise(seed, scale):
    def h(ix, iy):
        return (zlib.crc32(f"{seed}:{ix}:{iy}".encode()) & 0xFFFF) / 65535.0

    def f(x, y):
        gx, gy = x / scale, y / scale
        ix, iy = math.floor(gx), math.floor(gy)
        fx, fy = gx - ix, gy - iy
        sx, sy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
        a, b, c, d = h(ix, iy), h(ix + 1, iy), h(ix, iy + 1), h(ix + 1, iy + 1)
        return (a * (1 - sx) + b * sx) * (1 - sy) + (c * (1 - sx) + d * sx) * sy
    return f


# ---------------------------------------------------------------- palettes ----
# Each set is a dict of colours plus a pattern name.
PALETTES = {
    "MINERS": dict(pattern="canvas", base=(84, 100, 122), dark=(58, 70, 90), light=(112, 130, 154),
                   accent=(236, 176, 40), accent2=(232, 232, 220), metal=(150, 154, 162), boot=(72, 50, 34)),
    "COAL": dict(pattern="plates", base=(40, 42, 50), dark=(22, 24, 30), light=(96, 104, 120),
                 accent=(214, 104, 34), accent2=(150, 160, 178), metal=(120, 128, 142), boot=(30, 30, 36)),
    "STEPPE": dict(pattern="camo", base=(178, 160, 108), dark=(86, 68, 40), light=(208, 192, 140),
                   mid=(122, 122, 70), accent=(244, 244, 244), accent2=(90, 80, 52), metal=(96, 92, 80),
                   boot=(60, 44, 30)),
    "TERRICONE": dict(pattern="camo", base=(78, 80, 86), dark=(40, 42, 46), light=(112, 116, 122),
                      mid=(54, 56, 62), accent=(232, 126, 36), accent2=(112, 66, 46), metal=(96, 98, 104),
                      boot=(28, 28, 30), rust=(116, 68, 46)),
}


def surface(pal, name, w=64, h=64):
    """Return f(face_key, p, y) -> RGBA for the base cloth/plate of a set."""
    n1, n2, n3 = vnoise(name + "a", 4.5), vnoise(name + "b", 3.2), vnoise(name + "c", 1.5)
    r = rng(name + "_px")

    def camo(_face, p, y):
        a, b = n1(p, y), n2(p + 31, y + 17)
        if a > 0.64:
            c = pal["dark"]
        elif b > 0.60:
            c = pal["mid"]
        elif pal.get("rust") and a < 0.20:
            c = pal["rust"]
        else:
            c = pal["base"]
        d = int((n3(p, y) - 0.5) * 22)
        return rgba(shade(c, d))

    def canvas(_face, p, y):
        weave = -5 if (int(p) + int(y)) % 2 == 0 else 3
        patch = -14 if n1(p + 5, y + 9) > 0.78 else 0
        return rgba(shade(pal["base"], weave + patch + int((n3(p, y) - 0.5) * 10)))

    def plates(_face, p, y):
        row, col = int(y) // 4, int(p + (2 if (int(y) // 4) % 2 else 0)) // 5
        tint = (zlib.crc32(f"{name}{row}{col}".encode()) & 0xFF) / 255.0
        c = shade(pal["base"], int((tint - 0.5) * 26))
        if int(y) % 4 == 3 or int(p + (2 if row % 2 else 0)) % 5 == 4:
            c = shade(pal["dark"], int((n3(p, y) - 0.5) * 10))
        elif int(y) % 4 == 0 and tint > 0.55:
            c = shade(pal["light"], -40)
        return rgba(c)

    return {"camo": camo, "canvas": canvas, "plates": plates}[pal["pattern"]]


# ------------------------------------------------------------------- boxes ----
def box_faces(u, v, w, h, d):
    return {
        "top": (u + d, v, w, d), "bottom": (u + d + w, v, w, d),
        "right": (u, v + d, d, h), "front": (u + d, v + d, w, h),
        "left": (u + d + w, v + d, d, h), "back": (u + 2 * d + w, v + d, w, h),
    }


def paint_box(img, u, v, w, h, d, fn):
    """Call fn(face, p, y, lx, ly, fw, fh) for every texel of the six faces; None leaves the texel unchanged.
    p is a continuous coordinate around the four vertical faces (so patterns wrap without seams)."""
    offs = {"right": 0, "front": d, "left": d + w, "back": 2 * d + w}
    for face, (fx, fy, fw, fh) in box_faces(u, v, w, h, d).items():
        for ly in range(fh):
            for lx in range(fw):
                if face in offs:
                    p, y = offs[face] + lx, ly
                else:
                    p, y = lx + 40, ly + (60 if face == "top" else 90)
                c = fn(face, p, y, lx, ly, fw, fh)
                if c is not None:
                    img.putpixel((fx + lx, fy + ly), c)


def edge_dark(c, lx, ly, fw, fh, amount=-26):
    """Darken the outer texel ring of a face so pieces read as panels."""
    if lx in (0, fw - 1) or ly in (0, fh - 1):
        return shade(c, amount)
    return c


# --------------------------------------------------------- armour layer sheets ----
def armor_layers(mat):
    pal = PALETTES[mat]
    cloth = surface(pal, mat)
    l1 = Image.new("RGBA", (64, 32), (0, 0, 0, 0))
    l2 = Image.new("RGBA", (64, 32), (0, 0, 0, 0))

    # ---- layer 1: helmet (head), jacket (body + arms), boots (legs)
    def helmet(face, p, y, lx, ly, fw, fh):
        if face == "bottom":
            return None
        if face == "top":
            c = cloth(face, p, y)
        elif face == "front":
            if ly <= 2 or (ly <= 5 and lx in (0, fw - 1)):
                c = cloth(face, p, y)
            else:
                return None
        elif face in ("right", "left"):
            if ly > 4:
                return None
            c = cloth(face, p, y)
        else:  # back
            if ly > 6:
                return None
            c = cloth(face, p, y)
        if face == "front" and ly == 2:
            c = pal["accent2"] if mat in ("STEPPE", "TERRICONE") else pal["dark"]
        if mat == "MINERS":
            c = shade(pal["accent"], -(ly * 6) + (14 if face == "top" else 0))   # yellow hard hat
            if face == "front" and ly <= 1 and lx in (3, 4):
                c = (250, 250, 214, 255)                                         # head lamp
            if face == "front" and ly == 2:
                c = shade(pal["accent"], -50)
        if mat == "COAL" and face in ("front", "right", "left") and ly == 0:
            c = shade(pal["accent"], -10)                                        # ember crest line
        return rgba(edge_dark(rgba(c), lx, ly, fw, fh, -18))

    paint_box(l1, 0, 0, 8, 8, 8, helmet)

    def jacket(face, p, y, lx, ly, fw, fh):
        c = cloth(face, p, y)
        if face in ("top", "bottom"):
            return rgba(shade(c, -12))
        if mat == "MINERS":
            if ly in (6, 7):                                                     # reflective stripes
                c = pal["accent"] if (int(p) % 8) < 6 else shade(pal["accent"], -40)
        elif mat == "COAL" and ly == 5:
            c = shade(pal["accent"], -20)
        elif mat in ("STEPPE", "TERRICONE"):
            if face == "front" and ly in (3, 4, 5) and lx in (1, 2, 5, 6):       # chest pockets
                c = shade(c, -22)
            if face == "front" and ly <= 1 and lx in (3, 4):
                c = shade(pal["light"], -10)                                     # collar
        return rgba(edge_dark(rgba(c), lx, ly, fw, fh))

    paint_box(l1, 16, 16, 8, 12, 4, jacket)

    def sleeve(face, p, y, lx, ly, fw, fh):
        c = cloth(face, p + 11, y)
        if face in ("top", "bottom"):
            return rgba(shade(c, -10 if face == "top" else -26))
        if ly >= 9:
            c = shade(pal["dark"], 6)                                            # cuff
        if mat in ("STEPPE", "TERRICONE") and ly == 2 and face in ("front", "back", "left", "right"):
            c = pal["accent"] if mat == "STEPPE" else pal["accent2"]             # unit armband
        if mat == "MINERS" and ly == 6:
            c = pal["accent"]
        return rgba(edge_dark(rgba(c), lx, ly, fw, fh, -20))

    paint_box(l1, 40, 16, 4, 12, 4, sleeve)

    def boots(face, p, y, lx, ly, fw, fh):
        if face == "top":
            return None
        if face != "bottom" and ly < 8:
            return None
        if face == "bottom":
            return rgba(shade(pal["boot"], -22))
        c = shade(pal["boot"], int((vnoise(mat + "bt", 1.4)(p, y) - 0.5) * 18))
        if ly == 8:
            c = shade(pal["metal"], -10) if mat != "MINERS" else shade(pal["boot"], 22)  # cuff
        if ly == 11 and face != "bottom":
            c = shade(pal["boot"], -26)                                          # sole
        if mat == "COAL" and ly in (9, 10) and face == "front":
            c = shade(pal["dark"], 4)
        return rgba(edge_dark(rgba(c), lx, ly, fw, fh, -14))

    paint_box(l1, 0, 16, 4, 12, 4, boots)

    # ---- layer 2: trousers (legs) and the belt line (body)
    def trousers(face, p, y, lx, ly, fw, fh):
        c = cloth(face, p + 5, y + 3)
        if face in ("top", "bottom"):
            return rgba(shade(c, -16))
        if ly >= 10:
            c = shade(c, -14)
        if ly in (5, 6) and face == "front":
            c = shade(c, -16)                                                    # knee pads
        if mat == "MINERS" and face in ("front", "back") and ly == 4:
            c = pal["accent"]
        return rgba(edge_dark(rgba(c), lx, ly, fw, fh, -16))

    paint_box(l2, 0, 16, 4, 12, 4, trousers)

    def belt(face, p, y, lx, ly, fw, fh):
        if face in ("top", "bottom") or ly < 8:
            return None
        c = shade(pal["boot"], 6) if ly in (8, 9) else shade(cloth(face, p, y), -10)
        if ly in (8, 9) and face == "front" and lx in (3, 4):
            c = pal["metal"]                                                     # buckle
        return rgba(c)

    paint_box(l2, 16, 16, 8, 12, 4, belt)
    return l1, l2


# ---------------------------------------------------------------- item icons ----
MASKS = {
    "HELMET": [
        "................", "................", "................", ".....######.....", "....########....",
        "...##########...", "...##########...", "...##########...", "...###....###...", "...###....###...",
        "................", "................", "................", "................", "................",
        "................"],
    "CHESTPLATE": [
        "................", "..####....####..", ".#####....#####.", ".##############.", ".##############.",
        ".##############.", ".###.######.###.", ".###.######.###.",
        ".###.######.###.", "..##.######.##..", ".....######.....", ".....######.....", "................",
        "................", "................", "................"],
    "LEGGINGS": [
        "................", "................", "...##########...", "...##########...", "...##########...",
        "...##########...", "...####..####...", "...####..####...", "...####..####...", "...####..####...",
        "...####..####...", "...####..####...", "...####..####...", "...###....###...", "................",
        "................"],
    "BOOTS": [
        "................", "................", "................", "................", "................",
        "................", "..####....####..", "..####....####..", "..####....####..", "..####....####..",
        ".#####....#####.", "######....######", "######....######", "................", "................",
        "................"],
}


def armor_icon(mat, slot):
    pal = PALETTES[mat]
    cloth = surface(pal, mat + slot)
    mask = MASKS[slot]
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    solid = {(x, y) for y, row in enumerate(mask) for x, ch in enumerate(row) if ch == "#"}
    for (x, y) in solid:
        c = rgba(cloth("icon", x * 1.0, y * 1.0))
        c = shade(c, 10 - (x + y) // 2 + 8)                                      # light from the top-left
        if mat == "MINERS" and slot == "HELMET":
            c = shade(pal["accent"], -(y - 3) * 6)
        im.putpixel((x, y), c)
    for (x, y) in solid:                                                        # outline pass
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + dx, y + dy) not in solid:
                im.putpixel((x, y), shade(im.getpixel((x, y)), -42))
                break
    # per-slot accents
    if slot == "HELMET":
        if mat == "MINERS":
            im.putpixel((7, 4), (250, 250, 214, 255))
            im.putpixel((8, 4), (250, 250, 214, 255))
        for x in range(4, 12):
            if (x, 7) in solid:
                im.putpixel((x, 7), shade(pal["accent2"] if mat in ("STEPPE", "TERRICONE") else pal["dark"], 0))
    elif slot == "CHESTPLATE":
        for x in range(3, 13):
            if (x, 5) in solid and mat in ("MINERS", "COAL"):
                im.putpixel((x, 5), shade(pal["accent"], -10))
        if mat in ("STEPPE", "TERRICONE"):
            for (x, y) in ((5, 7), (6, 7), (9, 7), (10, 7)):
                im.putpixel((x, y), shade(im.getpixel((x, y)), -26))
    elif slot == "LEGGINGS":
        for x in range(3, 13):
            if (x, 2) in solid:
                im.putpixel((x, 2), shade(pal["boot"], 8))
    elif slot == "BOOTS":
        for (x, y) in solid:
            if y >= 11:
                im.putpixel((x, y), shade(pal["boot"], -14 + (x % 2) * 6))
    return im


# ---- other item icons ----------------------------------------------------------
def i_cartridge(_n):
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for cx in (4, 7, 10):
        for y in range(5, 13):
            c = (214, 168, 70, 255) if y >= 7 else (176, 100, 52, 255)           # brass case, copper tip
            im.putpixel((cx, y), shade(c, -(y - 5) * 3))
            im.putpixel((cx + 1, y), shade(c, -22 - (y - 5) * 3))
        im.putpixel((cx, 4), (190, 112, 56, 255))
        im.putpixel((cx + 1, 4), (150, 84, 44, 255))
        im.putpixel((cx, 13), (120, 88, 40, 255))
        im.putpixel((cx + 1, 13), (96, 70, 34, 255))
    return im


def i_magazine(_n):
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    pts = [(5, 2), (6, 3), (6, 4), (7, 5), (7, 6), (8, 7), (8, 8), (9, 9), (9, 10), (10, 11), (10, 12), (11, 13)]
    for i, (x, y) in enumerate(pts):
        for dx in range(0, 4):
            col = (62, 66, 76, 255) if dx in (0, 3) else (96, 102, 116, 255)
            if dx == 1:
                col = (124, 132, 148, 255)
            im.putpixel((x + dx - 1 if x + dx - 1 < 16 else 15, y), shade(col, -(i * 2)))
    for x in range(4, 9):
        im.putpixel((x, 2), (150, 156, 170, 255))
    return im


def i_gun_parts(_n):
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    r = rng("gun_parts")
    for (cx, cy, rad) in ((5, 6, 3), (10, 10, 2)):                                # two gears
        for y in range(16):
            for x in range(16):
                d = math.hypot(x - cx, y - cy)
                if d <= rad + 0.3 and d >= 0.9:
                    im.putpixel((x, y), shade((130, 136, 150, 255), r.randint(-14, 8)))
    for x in range(2, 14):                                                      # a spring
        im.putpixel((x, 13), (170, 176, 188, 255) if x % 2 else (96, 100, 112, 255))
    for y in range(2, 6):                                                       # a bolt
        im.putpixel((12, y), (110, 114, 128, 255))
        im.putpixel((13, y), (78, 82, 92, 255))
    im.putpixel((12, 1), (150, 156, 170, 255))
    im.putpixel((13, 1), (150, 156, 170, 255))
    return im


def i_coal_plate(_n):
    pal = PALETTES["COAL"]
    cloth = surface(pal, "coal_plate_icon")
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for y in range(3, 13):
        for x in range(2, 14):
            c = rgba(cloth("icon", x, y))
            im.putpixel((x, y), c)
    for x in range(2, 14):
        im.putpixel((x, 3), (110, 118, 134, 255))
        im.putpixel((x, 12), (16, 18, 22, 255))
    for y in range(3, 13):
        im.putpixel((2, y), (96, 104, 120, 255))
        im.putpixel((13, y), (16, 18, 22, 255))
    for (x, y) in ((4, 5), (11, 5), (4, 10), (11, 10)):                          # rivets
        im.putpixel((x, y), (180, 190, 206, 255))
    return im


def i_rifle(_n):
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    wood, wood_d, wood_l = (122, 78, 40, 255), (92, 58, 30, 255), (150, 100, 56, 255)
    steel, steel_d, steel_l = (66, 70, 80, 255), (40, 42, 50, 255), (110, 116, 130, 255)

    def px(x, y, c):
        if 0 <= x < 16 and 0 <= y < 16:
            im.putpixel((x, y), c)

    for i in range(14):                                                          # along the diagonal
        x, y = 1 + i, 14 - i
        if i <= 3:                                                               # wooden stock, 3 px thick
            px(x, y, wood)
            px(x + 1, y, wood_d)
            px(x, y - 1, wood_l)
            px(x, y + 1, wood_d)
            px(x + 1, y + 1, wood_d)
        elif i <= 7:                                                             # receiver
            px(x, y, steel)
            px(x + 1, y, steel_d)
            px(x, y - 1, steel_l)
            px(x, y + 1, steel_d)
            px(x + 1, y + 1, steel_d)
        elif i <= 10:                                                            # handguard
            px(x, y, wood)
            px(x + 1, y, wood_d)
            px(x, y - 1, wood_l)
            px(x, y + 1, wood_d)
        else:                                                                    # barrel
            px(x, y, steel_d)
            px(x, y - 1, steel_l)
            px(x + 1, y, steel_d)
    px(14, 0, steel_l)                                                           # front sight
    px(14, 1, steel_d)
    for (x, y) in ((8, 9), (9, 10), (9, 11), (10, 12)):                          # curved magazine
        px(x, y, steel_d)
        px(x + 1, y, steel)
    px(10, 13, steel_d)
    for (x, y) in ((6, 9), (5, 10), (5, 11)):                                    # pistol grip
        px(x, y, wood_d)
    px(7, 9, steel_l)
    return im


def i_rifle_model(_n):
    """Colour swatches (4x4 px each) for the 3D rifle model; the layout is tools/rifle_model.py: SWATCHES."""
    import random
    from rifle_model import SWATCHES
    base = {
        "steel_dark": (44, 47, 54), "steel_mid": (72, 76, 86), "steel_light": (118, 124, 138), "black": (16, 17, 20),
        "wood_dark": (96, 60, 30), "wood_mid": (128, 82, 42), "wood_light": (156, 106, 58), "wood_grain": (108, 70, 36),
        "magazine": (58, 56, 50), "brass": (184, 138, 52), "highlight": (170, 176, 188), "mark": (140, 44, 38),
    }
    rng = random.Random(1730)
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 255))
    for name, (col, row) in SWATCHES.items():
        r, g, b = base[name]
        for y in range(4):
            for x in range(4):
                d = rng.randint(-5, 5)
                if name.startswith("wood") and x in (1, 2):                      # a darker grain line
                    d -= 7 if (x + y) % 2 == 0 else 2
                if name == "magazine" and y in (1, 3):                           # ribs of the pressed magazine
                    d += 9
                im.putpixel((col * 4 + x, row * 4 + y),
                            (max(0, min(255, r + d)), max(0, min(255, g + d)), max(0, min(255, b + d)), 255))
    return im


# ---------------------------------------------------------------- entity skins ----
SKIN = (196, 150, 118)
SKIN_D = (170, 126, 98)
HAIR_M = (52, 36, 26)
HAIR_F = (36, 30, 26)


def skin_noise(name):
    n = vnoise(name, 1.8)
    return lambda x, y: int((n(x, y) - 0.5) * 12)


def militia_skin(mat, armband, hair):
    pal = PALETTES[mat]
    cloth = surface(pal, "militia_" + mat)
    sk = skin_noise("sk" + mat)
    im = Image.new("RGBA", (64, 64), (0, 0, 0, 0))

    def head(face, p, y, lx, ly, fw, fh):
        c = SKIN if face != "bottom" else SKIN_D
        c = shade(c, sk(p, y))
        if face == "top":
            c = shade(hair, sk(p, y))
        elif face == "front":
            if ly <= 1:
                c = shade(hair, sk(p, y))
            elif ly == 3 and lx in (1, 2, 5, 6):
                c = shade(hair, 6)                                               # brows
            elif ly == 4 and lx in (1, 2, 5, 6):
                c = (236, 236, 236, 255) if lx in (1, 6) else (66, 86, 60, 255)  # eyes
            elif ly >= 6 and ly <= 7 and 1 <= lx <= 6:
                c = shade(c, -10)                                                # stubble
            elif ly == 5 and lx in (3, 4):
                c = shade(c, -12)                                                # nose shadow
        elif face in ("right", "left"):
            if ly <= 2:
                c = shade(hair, sk(p, y))
        elif face == "back":
            if ly <= 4:
                c = shade(hair, sk(p, y))
        return rgba(c)

    paint_box(im, 0, 0, 8, 8, 8, head)

    def uniform(face, p, y, lx, ly, fw, fh, offset=0):
        c = cloth(face, p + offset, y)
        if face in ("top", "bottom"):
            return rgba(shade(c, -14))
        return rgba(edge_dark(rgba(c), lx, ly, fw, fh, -12))

    def body(face, p, y, lx, ly, fw, fh):
        c = uniform(face, p, y, lx, ly, fw, fh)
        if face == "front" and ly in (3, 4, 5) and lx in (1, 2, 5, 6):
            c = shade(c, -24)
        if ly >= 10 and face not in ("top", "bottom"):
            c = shade(pal["boot"], 12) if ly == 10 else c                        # belt
        return c

    paint_box(im, 16, 16, 8, 12, 4, body)

    def arm(face, p, y, lx, ly, fw, fh):
        if ly >= 10 and face not in ("top", "bottom"):
            return rgba(shade(SKIN, sk(p, y)))                                   # bare hands
        c = uniform(face, p, y, lx, ly, fw, fh, 9)
        if ly in (2, 3) and face not in ("top", "bottom"):
            c = rgba(armband)                                                    # faction armband
        return c

    paint_box(im, 40, 16, 4, 12, 4, arm)     # right arm
    paint_box(im, 32, 48, 4, 12, 4, arm)     # left arm

    def leg(face, p, y, lx, ly, fw, fh):
        if ly >= 9 and face != "top":
            return rgba(shade(pal["boot"], int((vnoise("lg", 1.2)(p, y) - 0.5) * 14)))
        return uniform(face, p, y, lx, ly, fw, fh, 21)

    paint_box(im, 0, 16, 4, 12, 4, leg)      # right leg
    paint_box(im, 16, 48, 4, 12, 4, leg)     # left leg
    return im


def miner_skin():
    """Villager-layout (64x64) texture: soot-smudged miner in a work coat and a yellow hard hat."""
    pal = PALETTES["MINERS"]
    cloth = surface(pal, "miner_coat")
    sk = skin_noise("miner_sk")
    im = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    hat, hat_d, hat_l = (236, 184, 40), (190, 144, 28), (252, 214, 96)
    soot = (58, 46, 40)

    def head(face, p, y, lx, ly, fw, fh):          # 8 x 10 x 8
        c = shade((176, 128, 98), sk(p, y))
        if face == "bottom":
            return rgba(shade(c, -20))
        if face == "top" or ly <= 1:               # hard hat dome
            return rgba(shade(hat if (lx + ly) % 5 else hat_l, -(ly * 4) + (10 if face == "top" else 0)))
        if face in ("front", "left", "right", "back") and ly == 2:
            return rgba(hat_d)                     # brim line
        if face == "front":
            if ly == 3 and lx in (3, 4):
                return (250, 250, 214, 255)        # head lamp is on the hat: bright forehead glow
            if ly == 5 and lx in (1, 2, 5, 6):
                return (236, 236, 236, 255) if lx in (1, 6) else (52, 78, 52, 255)
            if ly == 4 and lx in (1, 2, 5, 6):
                return rgba(shade(HAIR_F, 10))
            if ly in (8, 9) and 1 <= lx <= 6:
                return rgba(shade(c, -16))         # beard stubble
            if ly in (6, 7) and lx in (0, 7):
                return rgba(soot)                  # soot smudges
        if face in ("left", "right") and ly >= 6:
            return rgba(shade(c, -8))
        if face == "back" and ly >= 3:
            return rgba(shade(HAIR_M, sk(p, y)))
        return rgba(c)

    paint_box(im, 0, 0, 8, 10, 8, head)

    def nose(face, p, y, lx, ly, fw, fh):
        return rgba(shade((166, 118, 90), sk(p, y)))

    paint_box(im, 24, 0, 2, 4, 2, nose)

    def coat(face, p, y, lx, ly, fw, fh, tall=12, off=0):
        c = cloth(face, p + off, y)
        if face in ("top", "bottom"):
            return rgba(shade(c, -16))
        if ly in (6, 7) and tall == 12:            # reflective stripes (orange)
            c = pal["accent"] if (int(p) % 8) < 6 else shade(pal["accent"], -40)
        return rgba(edge_dark(rgba(c), lx, ly, fw, fh, -14))

    paint_box(im, 16, 20, 8, 12, 6, lambda *a: coat(*a))                          # body

    def apron(face, p, y, lx, ly, fw, fh):         # long coat skirt: the part below the body
        if face in ("top", "bottom"):
            return None
        c = shade(pal["dark"], int((vnoise("ap", 1.6)(p, y) - 0.5) * 14))
        if ly >= 12:
            c = shade(c, -8 if ly % 2 else 4)
        if ly in (16, 17) and face in ("front", "back"):
            c = rgba(soot)
        return rgba(edge_dark(rgba(c), lx, ly, fw, fh, -10))

    paint_box(im, 0, 38, 8, 20, 6, apron)                                         # jacket overlay (coat skirt)

    def arm(face, p, y, lx, ly, fw, fh):
        if ly >= 6 and face not in ("top", "bottom"):
            return rgba(shade((176, 128, 98), sk(p, y)))
        return coat(face, p, y, lx, ly, fw, fh, tall=8, off=7)

    paint_box(im, 44, 22, 4, 8, 4, arm)                                           # crossed arms (outer)

    def bar(face, p, y, lx, ly, fw, fh):
        if face in ("front", "back") and 1 <= ly <= 3:
            return rgba(shade(pal["dark"], int((vnoise("br", 1.3)(p, y) - 0.5) * 12)))
        return rgba(shade((176, 128, 98), sk(p, y))) if lx in (0, fw - 1) else coat(face, p, y, lx, ly, fw, fh, tall=4)

    paint_box(im, 40, 38, 8, 4, 4, bar)                                           # crossed forearms

    def leg(face, p, y, lx, ly, fw, fh):
        if ly >= 9 and face != "top":
            return rgba(shade(pal["boot"], int((vnoise("mb", 1.2)(p, y) - 0.5) * 14)))
        c = shade((52, 56, 66), int((vnoise("ml", 1.5)(p, y) - 0.5) * 12))
        if face in ("top", "bottom"):
            return rgba(shade(c, -12))
        return rgba(edge_dark(rgba(c), lx, ly, fw, fh, -10))

    paint_box(im, 0, 22, 4, 12, 4, leg)
    return im


# ---------------------------------------------------------- boss items ----
def i_siren(_n):
    """Factory siren: an orange horn on a steel mount with a white band."""
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    r = rng("siren_icon")

    def px(x, y, c):
        if 0 <= x < 16 and 0 <= y < 16:
            im.putpixel((x, y), c)

    steel, steel_d, steel_l = (84, 90, 104, 255), (44, 48, 58, 255), (140, 148, 164, 255)
    for x in range(4, 12):                                                      # mount plate
        px(x, 13, steel_d)
        px(x, 14, steel_d)
        px(x, 12, steel)
    for y in range(9, 13):                                                      # post
        px(7, y, steel)
        px(8, y, steel_d)
    for x in range(2, 14):                                                      # the horn widens to the right
        half = 1 + int((x - 2) * 0.42)
        for y in range(7 - half, 7 + half + 1):
            c = (214, 104, 34, 255) if y < 7 + half - 1 else (150, 66, 22, 255)
            if y == 7 - half:
                c = (248, 160, 80, 255)                                          # lit top edge
            if x in (6, 7):
                c = (236, 236, 228, 255) if y not in (7 - half, 7 + half) else (200, 200, 192, 255)   # white band
            px(x, y, shade(c, r.randint(-6, 4)))
    for y in range(7 - 3, 7 + 4):                                               # the dark mouth of the horn
        px(13, y, (30, 24, 22, 255))
    px(1, 7, steel_l)
    px(2, 6, steel_l)
    px(2, 8, steel)
    return im


def i_director_pickaxe(_n):
    """The director's pickaxe: white-gold head, black tips, dark handle with a gold band."""
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for i in range(10):
        x, y = 2 + i, 13 - i
        im.putpixel((x, y), (70, 52, 38, 255) if i % 3 else (58, 42, 30, 255))
        if i == 4:
            im.putpixel((x, y), (232, 190, 60, 255))                             # gold band
    head = [(3, 7), (4, 6), (5, 5), (6, 4), (7, 3), (8, 3), (9, 3), (10, 3), (11, 4), (12, 5), (13, 6), (13, 7)]
    for (x, y) in head:
        im.putpixel((x, y), (232, 190, 60, 255))
    for (x, y) in head[1:-1]:
        if y + 1 <= 6 and im.getpixel((x, y + 1))[3] == 0:
            im.putpixel((x, y + 1), (176, 134, 34, 255))
    for (x, y) in ((6, 4), (7, 3), (8, 3), (9, 3)):
        im.putpixel((x, y), (255, 238, 150, 255))
    for (x, y) in ((3, 7), (13, 7)):
        im.putpixel((x, y), (28, 28, 32, 255))
    return im


def i_director_badge(_n):
    """A gold badge on a red-and-white ribbon: a lamp in a gear (no real insignia)."""
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))

    def px(x, y, c):
        if 0 <= x < 16 and 0 <= y < 16:
            im.putpixel((x, y), c)

    for y in range(0, 6):                                                       # ribbon, folded into a V
        px(5 + y // 2, y, (200, 40, 36, 255))
        px(6 + y // 2, y, (236, 236, 228, 255))
        px(10 - y // 2, y, (200, 40, 36, 255))
        px(9 - y // 2, y, (236, 236, 228, 255))
    for y in range(16):
        for x in range(16):
            d = math.hypot(x - 7.5, y - 10.0)
            if 3.2 < d <= 4.9:
                px(x, y, (176, 134, 34, 255))                                   # rim
            elif d <= 3.2:
                px(x, y, (240, 200, 70, 255) if (x + y) % 4 else (255, 226, 120, 255))
    for (x, y) in ((7, 8), (8, 8), (7, 9), (8, 9), (7, 10), (8, 10)):           # lamp
        px(x, y, (60, 44, 20, 255))
    px(7, 11, (60, 44, 20, 255))
    px(8, 11, (60, 44, 20, 255))
    px(7, 7, (255, 250, 200, 255))
    px(8, 7, (255, 250, 200, 255))
    return im


# ---------------------------------------------------------------- boss skin ----
def director_skin():
    """The Combine Director: grey hair and moustache, white hard hat, charcoal suit, red tie (zombie 64x64 layout)."""
    sk = skin_noise("director_sk")
    suit = surface(dict(pattern="canvas", base=(56, 60, 70), dark=(36, 38, 46), light=(80, 84, 96)), "director_suit")
    im = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    hat, hat_d = (240, 240, 232), (196, 196, 188)
    grey = (150, 150, 150)

    def head(face, p, y, lx, ly, fw, fh):
        c = shade(SKIN if face != "bottom" else SKIN_D, sk(p, y))
        if face == "top" or (face != "bottom" and ly <= 1):
            return rgba(shade(hat, -6 * ly if face != "top" else 0))
        if face != "bottom" and ly == 2:
            return rgba(hat_d)                                                  # the brim
        if face == "front":
            if ly == 3 and lx in (1, 2, 5, 6):
                return rgba(shade(grey, -20))                                   # heavy brows
            if ly == 4 and lx in (1, 2, 5, 6):
                return (236, 236, 236, 255) if lx in (1, 6) else (60, 44, 34, 255)
            if ly == 6 and 1 <= lx <= 6 and lx not in (3, 4):
                return rgba(shade(grey, -8))                                    # moustache
            if ly == 5 and lx in (3, 4):
                return rgba(shade(c, -14))
        if face in ("left", "right") and 3 <= ly <= 4:
            return rgba(shade(grey, sk(p, y)))                                  # grey temples
        if face == "back" and 3 <= ly <= 5:
            return rgba(shade(grey, sk(p, y)))
        return rgba(c)

    paint_box(im, 0, 0, 8, 8, 8, head)

    def body(face, p, y, lx, ly, fw, fh):
        c = suit(face, p, y)
        if face in ("top", "bottom"):
            return rgba(shade(c, -14))
        if face == "front":
            if (ly == 0 and 2 <= lx <= 5) or (ly in (1, 2, 3) and lx in (3, 4)):
                c = (236, 236, 230, 255)                                        # shirt
            if ly >= 1 and lx in (3, 4) and ly <= 7:
                c = (190, 36, 34, 255) if lx == 3 else (150, 28, 26, 255)       # tie
            if ly in (8, 10) and lx in (2, 5):
                c = (200, 164, 60, 255)                                         # brass buttons
            if ly == 4 and lx == 1:
                c = (232, 190, 60, 255)                                         # badge of merit on the lapel
        if ly >= 10:
            c = (48, 34, 26, 255)                                               # belt
        return rgba(edge_dark(rgba(c), lx, ly, fw, fh, -12))

    paint_box(im, 16, 16, 8, 12, 4, body)

    def arm(face, p, y, lx, ly, fw, fh):
        if ly == 11 and face not in ("top", "bottom"):
            return rgba(shade(SKIN, sk(p, y)))                                  # hands
        if ly == 10 and face not in ("top", "bottom"):
            return (236, 236, 230, 255)                                         # shirt cuffs
        c = suit(face, p + 9, y)
        return rgba(edge_dark(rgba(shade(c, -10 if face in ("top", "bottom") else 0)), lx, ly, fw, fh, -12))

    paint_box(im, 40, 16, 4, 12, 4, arm)
    paint_box(im, 32, 48, 4, 12, 4, arm)

    def leg(face, p, y, lx, ly, fw, fh):
        if ly >= 10 and face != "top":
            return (22, 22, 26, 255)                                            # polished shoes
        c = shade((48, 50, 58), int((vnoise("dl", 1.5)(p, y) - 0.5) * 10))
        if face == "front" and lx in (1, 2):
            c = shade(c, 8)                                                     # trouser crease
        return rgba(edge_dark(rgba(c), lx, ly, fw, fh, -10))

    paint_box(im, 0, 16, 4, 12, 4, leg)
    paint_box(im, 16, 48, 4, 12, 4, leg)
    return im


# ------------------------------------------------------------------- driver ----
def save(im, directory, name):
    os.makedirs(directory, exist_ok=True)
    im.save(os.path.join(directory, name + ".png"))


def main():
    from content import ARMOR_SETS
    count = 0
    for name, fn in (("rifle_cartridge", i_cartridge), ("rifle_magazine", i_magazine), ("gun_parts", i_gun_parts),
                     ("coal_plate", i_coal_plate), ("ak_rifle", i_rifle), ("ak_rifle_model", i_rifle_model), ("combine_siren", i_siren),
                     ("director_pickaxe", i_director_pickaxe), ("director_badge", i_director_badge)):
        save(fn(name), ITEM_DIR, name)
        count += 1
    for mat, pieces in ARMOR_SETS.items():
        for pid, _names, slot in pieces:
            save(armor_icon(mat, slot), ITEM_DIR, pid)
            count += 1
        l1, l2 = armor_layers(mat)
        save(l1, ARMOR_DIR, mat.lower() + "_layer_1")
        save(l2, ARMOR_DIR, mat.lower() + "_layer_2")
        count += 2
    save(miner_skin(), ENTITY_DIR, "miner")
    save(militia_skin("STEPPE", (240, 240, 236), HAIR_M), ENTITY_DIR, "north_fighter")
    save(militia_skin("TERRICONE", (230, 120, 34), HAIR_F), ENTITY_DIR, "south_fighter")
    save(director_skin(), ENTITY_DIR, "combine_director")
    count += 4
    print(f"gear textures: {count} png files")


if __name__ == "__main__":
    main()

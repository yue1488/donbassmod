"""The 3D model of the AK (item/ak_rifle.json): cuboids + display transforms, single source for gen_resources.py,
gen_textures_gear.py and preview_ak.py.

Model space conventions (a block model, 16 units = 1 block, +y up):
    the BARREL points to -z (the "north" side, towards the muzzle), the STOCK is at +z,
    the MAGAZINE hangs below (-y), the sights are on top (+y), the ejection port / charging handle are on +x
    (the rifle's right side as seen by the shooter).
With this orientation the model needs NO rotation in the hands: in first person the item frame is the camera frame
(x right, y up, -z forward) and in third person, with the crossbow arm pose, the item frame is (x right, y up,
z backward) as well - see AkClientExtensions and the derivation in docs/AK_ORIENTATION.md.
"""

# 4x4 grid of 4x4-pixel colour swatches in textures/item/ak_rifle_model.png; (column, row)
SWATCHES = {
    "steel_dark": (0, 0), "steel_mid": (1, 0), "steel_light": (2, 0), "black": (3, 0),
    "wood_dark": (0, 1), "wood_mid": (1, 1), "wood_light": (2, 1), "wood_grain": (3, 1),
    "magazine": (0, 2), "brass": (1, 2), "highlight": (2, 2), "mark": (3, 2),
}

# the whole rifle is moved so that the pistol grip is at the centre of the model (where the hand holds an item)
SHIFT = (0.0, 1.2, -3.0)

# (name, material, from, to, rotation or None)  - pixels, before SHIFT
RAW_ELEMENTS = [
    ("muzzle_brake", "steel_dark", (7.3, 8.5, -2.0), (8.7, 9.9, -0.2), None),
    ("barrel", "steel_mid", (7.6, 8.8, -0.2), (8.4, 9.6, 6.0), None),
    ("front_sight_base", "steel_dark", (7.5, 9.6, 0.4), (8.5, 10.1, 1.6), None),
    ("front_sight_post", "steel_dark", (7.85, 10.1, 0.6), (8.15, 11.0, 0.9), None),
    ("gas_tube", "steel_mid", (7.5, 9.6, 2.8), (8.5, 10.3, 5.0), None),
    ("handguard_lower", "wood_mid", (6.9, 7.6, 3.2), (9.1, 9.6, 7.9), None),
    ("handguard_upper", "wood_dark", (7.2, 9.6, 4.4), (8.8, 10.5, 7.9), None),
    ("receiver", "steel_dark", (7.0, 7.4, 7.8), (9.0, 10.5, 11.8), None),
    ("receiver_cover", "steel_mid", (7.3, 10.5, 7.8), (8.7, 10.9, 11.6), None),
    ("rear_sight", "steel_dark", (7.6, 10.9, 8.0), (8.4, 11.5, 8.9), None),
    ("magazine", "magazine", (7.4, 1.6, 7.9), (8.6, 7.5, 9.5),
     {"angle": 22.5, "axis": "x", "origin": (8.0, 7.4, 8.7)}),
    ("trigger_guard", "steel_dark", (7.4, 6.7, 9.7), (8.6, 7.5, 10.9), None),
    ("pistol_grip", "wood_dark", (7.4, 4.2, 10.8), (8.6, 7.5, 12.0),
     {"angle": -22.5, "axis": "x", "origin": (8.0, 7.4, 11.4)}),
    ("stock_neck", "wood_mid", (7.4, 7.4, 11.7), (8.6, 9.8, 13.0), None),
    ("stock_butt", "wood_mid", (7.3, 5.6, 13.0), (8.7, 10.0, 14.4), None),
    ("butt_plate", "steel_dark", (7.25, 5.5, 14.4), (8.75, 10.1, 14.7), None),
    ("charging_handle", "steel_light", (9.0, 9.3, 9.0), (9.5, 9.8, 9.9), None),
    ("ejection_port", "black", (9.0, 8.7, 8.4), (9.04, 10.3, 10.6), None),
]

def bbox_centre():
    """Centre of the rifle's bounding box relative to the model centre (8, 8, 8), in pixels."""
    import math
    lo, hi = [1e9] * 3, [-1e9] * 3
    for _name, _mat, f, t, rot in RAW_ELEMENTS:
        pts = [[(t[a] if (i >> (2 - a)) & 1 else f[a]) + SHIFT[a] for a in range(3)] for i in range(8)]
        if rot:
            o = [rot["origin"][a] + SHIFT[a] for a in range(3)]
            ang = math.radians(rot["angle"])
            c, s = math.cos(ang), math.sin(ang)
            i1, i2 = {"x": (1, 2), "y": (2, 0), "z": (0, 1)}[rot["axis"]]
            for p in pts:
                u, v = p[i1] - o[i1], p[i2] - o[i2]
                p[i1], p[i2] = o[i1] + u * c - v * s, o[i2] + u * s + v * c
        for p in pts:
            for a in range(3):
                lo[a], hi[a] = min(lo[a], p[a]), max(hi[a], p[a])
    return [(lo[a] + hi[a]) / 2 - 8.0 for a in range(3)]


def _display():
    cx, cy, cz = bbox_centre()
    gs, fs = 0.9, 0.9        # icon / item frame scale: the rifle (~17 px long) has to fit into the 16 px slot
    return {
        # Hand contexts: identity rotation (see the module docstring), only a yaw of a few degrees that points the
        # barrel along the view: the crossbow arm pose skews the right arm by -0.3 rad towards the middle.
        # translation is in 1/16 block, applied in the frame of the context BEFORE the rotation.
        "thirdperson_righthand": {"rotation": [0, -15, 0], "translation": [0, 0, 0], "scale": [0.85, 0.85, 0.85]},
        "thirdperson_lefthand": {"rotation": [0, -15, 0], "translation": [0, 0, 0], "scale": [0.85, 0.85, 0.85]},
        "firstperson_righthand": {"rotation": [0, 10, 0], "translation": [-1.5, 4.2, -3], "scale": [1.0, 1.0, 1.0]},
        "firstperson_lefthand": {"rotation": [0, 10, 0], "translation": [-1.5, 4.2, -3], "scale": [1.0, 1.0, 1.0]},
        # side view for the icon: barrel to the right (a +y rotation of -90 turns -z into +x), centred in the slot
        "gui": {"rotation": [0, -90, 0],
                "translation": [round(gs * cz, 2), round(-gs * cy, 2), round(-gs * cx, 2)], "scale": [gs] * 3},
        # item frame: the viewer is on the -z side, so the same side view is a +90 turn
        "fixed": {"rotation": [0, 90, 0],
                  "translation": [round(-fs * cz, 2), round(-fs * cy, 2), round(fs * cx, 2)], "scale": [fs] * 3},
        "ground": {"rotation": [0, 0, 0], "translation": [0, 2, 0], "scale": [0.55, 0.55, 0.55]},
    }


DISPLAY = _display()


def _r(v):
    return round(v + 0.0, 3)


def swatch_uv(material):
    c, r = SWATCHES[material]
    return [c * 4 + 0.5, r * 4 + 0.5, c * 4 + 3.5, r * 4 + 3.5]


def elements():
    """The 'elements' array of the model JSON."""
    out = []
    for name, material, f, t, rot in RAW_ELEMENTS:
        el = {"name": name,
              "from": [_r(f[i] + SHIFT[i]) for i in range(3)],
              "to": [_r(t[i] + SHIFT[i]) for i in range(3)]}
        if rot:
            el["rotation"] = {"angle": rot["angle"], "axis": rot["axis"],
                              "origin": [_r(rot["origin"][i] + SHIFT[i]) for i in range(3)]}
        uv = swatch_uv(material)
        el["faces"] = {face: {"uv": uv, "texture": "#0"} for face in ("north", "east", "south", "west", "up", "down")}
        out.append(el)
    return out


def model_json(texture="donbass:item/ak_rifle_model", particle="donbass:item/ak_rifle"):
    return {"textures": {"0": texture, "particle": particle}, "gui_light": "front",
            "elements": elements(), "display": DISPLAY}

"""Procedural 16x16 pixel-art textures for the Donbass mod (PIL only, deterministic)."""
import os
import random
import zlib
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "main", "resources",
                    "assets", "donbass", "textures")
BLOCK_DIR = os.path.join(ROOT, "block")
ITEM_DIR = os.path.join(ROOT, "item")
S = 16


def rng(name):
    return random.Random(zlib.crc32(name.encode()))


def clamp(v):
    return max(0, min(255, int(v)))


def shade(c, d):
    return (clamp(c[0] + d), clamp(c[1] + d), clamp(c[2] + d), c[3] if len(c) > 3 else 255)


def new(fill=(0, 0, 0, 0)):
    im = Image.new("RGBA", (S, S), fill)
    return im


def noise(name, base, amp=14, size=None):
    r = rng(name)
    im = new()
    for y in range(S):
        for x in range(S):
            im.putpixel((x, y), shade(base, r.randint(-amp, amp)))
    return im


def speckle(im, name, color, count, amp=0):
    r = rng(name + "_sp")
    for _ in range(count):
        x, y = r.randrange(S), r.randrange(S)
        im.putpixel((x, y), shade(color, r.randint(-amp, amp)) if amp else color + (255,) if len(color) == 3 else color)
    return im


def bricks(name, brick, mortar, bw=8, bh=4, amp=10):
    r = rng(name)
    im = new()
    for y in range(S):
        row = y // bh
        off = (bw // 2) if row % 2 else 0
        for x in range(S):
            bx = (x + off) // bw
            tint = rng(f"{name}{row}_{bx}").randint(-amp, amp)
            if y % bh == bh - 1 or (x + off) % bw == bw - 1:
                c = shade(mortar, r.randint(-4, 4))
            else:
                c = shade(brick, tint + r.randint(-4, 4))
            im.putpixel((x, y), c)
    return im


def stone(name, base=(128, 128, 128), amp=14):
    return noise(name, base + (255,), amp)


def ore(name, base_im, spot, count=9, spot2=None):
    r = rng(name)
    im = base_im.copy()
    for _ in range(count):
        cx, cy = r.randint(1, 14), r.randint(1, 14)
        for dx, dy in r.sample([(0, 0), (1, 0), (0, 1), (-1, 0), (0, -1), (1, 1)], r.randint(2, 4)):
            x, y = cx + dx, cy + dy
            if 0 <= x < S and 0 <= y < S:
                c = spot if r.random() > 0.3 or not spot2 else spot2
                im.putpixel((x, y), shade(c + (255,), r.randint(-10, 10)))
    return im


def deepslate(name):
    r = rng(name)
    im = noise(name, (62, 62, 68, 255), 8)
    for y in range(S):
        if y % 5 == 2:
            for x in range(S):
                im.putpixel((x, y), shade(im.getpixel((x, y)), -10 + r.randint(-3, 3)))
    return im


def save(im, directory, name):
    os.makedirs(directory, exist_ok=True)
    im.save(os.path.join(directory, name + ".png"))


# ------------------------------------------------------------ block art ----
def t_mine_concrete(n):
    im = noise(n, (150, 150, 148, 255), 9)
    for y in range(S):
        for x in range(S):
            if x in (0, 15) or y in (0, 15):
                im.putpixel((x, y), shade(im.getpixel((x, y)), -22))
    return speckle(im, n, (110, 110, 108), 10, 6)


def t_reinforced(n):
    im = t_mine_concrete(n)
    for i in range(S):
        for k in (3, 12):
            im.putpixel((i, k), (70, 72, 78, 255))
            im.putpixel((k, i), (70, 72, 78, 255))
    for k in (3, 12):
        for j in (3, 12):
            im.putpixel((k, j), (150, 120, 90, 255))
    return im


def t_cracked(n):
    im = t_mine_concrete(n)
    r = rng(n + "c")
    x, y = r.randint(2, 6), 0
    while y < S:
        im.putpixel((x, y), (60, 60, 60, 255))
        y += 1
        x = max(0, min(15, x + r.choice([-1, 0, 0, 1])))
    x, y = 15, r.randint(5, 10)
    while x > 4:
        im.putpixel((x, y), (66, 66, 66, 255))
        x -= 1
        y = max(0, min(15, y + r.choice([-1, 0, 0, 1])))
    return im


def t_soot(n):
    im = t_mine_concrete(n)
    r = rng(n + "s")
    for y in range(S):
        f = (S - y) / S
        for x in range(S):
            c = im.getpixel((x, y))
            d = int(-70 * f * (0.5 + r.random() * 0.8))
            im.putpixel((x, y), shade(c, d))
    return im


def t_slag_block(n):
    im = noise(n, (112, 112, 116, 255), 12)
    for hx in (3, 11):
        for hy in (3, 11):
            for dx in range(3):
                for dy in range(3):
                    im.putpixel((hx + dx - 1, hy + dy - 1), (44, 44, 48, 255))
    for i in range(S):
        im.putpixel((i, 7), (84, 84, 88, 255))
        im.putpixel((7, i), (84, 84, 88, 255))
    return im


def t_slag_bricks(n):
    return bricks(n, (104, 104, 110), (70, 70, 76), 8, 4, 12)


def t_polished_slag(n):
    im = noise(n, (122, 124, 130, 255), 5)
    for i in range(S):
        im.putpixel((i, 0), (150, 152, 158, 255))
        im.putpixel((0, i), (146, 148, 154, 255))
        im.putpixel((i, 15), (90, 92, 98, 255))
        im.putpixel((15, i), (92, 94, 100, 255))
    return im


def t_sooty_bricks(n):
    im = bricks(n, (120, 70, 58), (82, 78, 74), 8, 4, 12)
    r = rng(n + "x")
    for y in range(S):
        for x in range(S):
            if r.random() < 0.25:
                im.putpixel((x, y), shade(im.getpixel((x, y)), -38))
    return im


def t_whitewash(n):
    im = noise(n, (232, 230, 222, 255), 7)
    return speckle(im, n, (200, 196, 186), 8, 6)


def t_clay_plaster(n):
    im = noise(n, (196, 160, 98, 255), 10)
    return speckle(im, n, (150, 112, 66), 12, 8)


def t_prefab(n):
    im = noise(n, (176, 178, 176, 255), 6)
    for i in range(S):
        im.putpixel((i, 0), (120, 122, 120, 255))
        im.putpixel((i, 15), (120, 122, 120, 255))
        im.putpixel((0, i), (120, 122, 120, 255))
        im.putpixel((15, i), (120, 122, 120, 255))
        im.putpixel((i, 8), (146, 148, 146, 255))
    for p in ((2, 2), (13, 2), (2, 13), (13, 13)):
        im.putpixel(p, (96, 98, 96, 255))
    return im


def t_slate(n):
    im = noise(n, (150, 152, 150, 255), 8)
    for x in range(S):
        wave = 1 if (x // 2) % 2 == 0 else -1
        for y in range(S):
            im.putpixel((x, y), shade(im.getpixel((x, y)), wave * 14))
    return im


def t_rusty_iron(n):
    im = noise(n, (150, 88, 52, 255), 18)
    r = rng(n + "r")
    for _ in range(30):
        x, y = r.randrange(S), r.randrange(S)
        im.putpixel((x, y), (96, 52, 30, 255))
    for _ in range(14):
        im.putpixel((r.randrange(S), r.randrange(S)), (190, 120, 66, 255))
    return im


def t_rusty_plate(n):
    im = t_rusty_iron(n)
    for i in range(S):
        im.putpixel((i, 0), (80, 44, 28, 255))
        im.putpixel((i, 15), (80, 44, 28, 255))
        im.putpixel((0, i), (80, 44, 28, 255))
        im.putpixel((15, i), (80, 44, 28, 255))
    for p in ((2, 2), (13, 2), (2, 13), (13, 13)):
        im.putpixel(p, (200, 140, 90, 255))
    return im


def t_factory_glass(n):
    im = new((190, 220, 228, 90))
    for i in range(S):
        for c in (0, 15, 7, 8):
            im.putpixel((i, c), (70, 76, 82, 255))
            im.putpixel((c, i), (70, 76, 82, 255))
    for i in range(3, 6):
        im.putpixel((i, i - 1), (240, 250, 255, 170))
    return im


def t_rusty_fence(n):
    im = new()
    for x in (0, 1, 7, 8, 14, 15):
        for y in range(S):
            im.putpixel((x, y), (126, 70, 40, 255) if x in (7, 8) else (110, 58, 34, 255))
    for y in (3, 4, 11, 12):
        for x in range(S):
            im.putpixel((x, y), (140, 80, 46, 255))
    r = rng(n)
    for _ in range(10):
        x, y = r.randrange(S), r.choice([3, 4, 11, 12, 7, 8])
        if im.getpixel((x, y))[3]:
            im.putpixel((x, y), (180, 110, 60, 255))
    return im


def t_chimney(n):
    im = new()
    for y in range(S):
        band = (y // 4) % 2 == 0
        base = (176, 70, 56) if band else (216, 208, 198)
        for x in range(S):
            rr = rng(f"{n}{x}{y}")
            c = shade(base + (255,), rr.randint(-8, 8))
            if y % 4 == 3:
                c = shade(c, -30)
            im.putpixel((x, y), c)
    return im


def t_hazard(n):
    im = new()
    for y in range(S):
        for x in range(S):
            yellow = ((x + y) // 4) % 2 == 0
            c = (232, 190, 28, 255) if yellow else (34, 34, 34, 255)
            im.putpixel((x, y), shade(c, rng(f"{n}{x}{y}").randint(-6, 6)))
    return im


def t_girder_side(n):
    im = noise(n, (104, 108, 118, 255), 6)
    for y in range(S):
        for x in range(S):
            if y in (0, 1, 14, 15):
                im.putpixel((x, y), (138, 142, 152, 255))
            elif x in (6, 7, 8, 9):
                im.putpixel((x, y), (126, 130, 140, 255))
    for p in ((1, 7), (14, 7), (1, 8), (14, 8)):
        im.putpixel(p, (60, 62, 70, 255))
    return im


def t_girder_end(n):
    im = new((70, 74, 84, 255))
    for y in range(S):
        for x in range(S):
            if y in (0, 1, 14, 15) or 6 <= x <= 9:
                im.putpixel((x, y), (138, 142, 152, 255))
    return im


def t_spoil_rock(n):
    im = noise(n, (92, 90, 90, 255), 20)
    return speckle(im, n, (52, 52, 54), 18, 8)


def t_burnt_spoil(n):
    im = noise(n, (148, 78, 58, 255), 20)
    return speckle(im, n, (92, 44, 34), 16, 10)


def t_spoil_gravel(n):
    r = rng(n)
    im = new()
    for y in range(S):
        for x in range(S):
            v = r.choice([48, 60, 72, 86, 98, 40])
            im.putpixel((x, y), (v, v, v + 2, 255))
    return im


def t_coal_shale(n):
    im = noise(n, (58, 58, 62, 255), 8)
    for y in range(S):
        if y % 4 == 1:
            for x in range(S):
                im.putpixel((x, y), shade(im.getpixel((x, y)), -16))
        if y % 4 == 3:
            for x in range(S):
                im.putpixel((x, y), shade(im.getpixel((x, y)), 10))
    return im


def t_smoldering(n):
    im = noise(n, (60, 46, 44, 255), 10)
    r = rng(n + "g")
    for _ in range(14):
        x, y = r.randrange(S), r.randrange(S)
        im.putpixel((x, y), r.choice([(236, 110, 30, 255), (255, 170, 40, 255), (200, 60, 24, 255)]))
        if r.random() < 0.5 and x < 15:
            im.putpixel((x + 1, y), (190, 70, 26, 255))
    return im


def t_coal_seam(n):
    base = stone(n + "b", (126, 126, 126), 10)
    im = base.copy()
    r = rng(n)
    for y in (3, 4, 9, 10, 11):
        for x in range(S):
            if r.random() < 0.92:
                im.putpixel((x, y), shade((24, 24, 28, 255), r.randint(-6, 8)))
    for _ in range(10):
        im.putpixel((r.randrange(S), r.randint(2, 12)), (70, 70, 76, 255))
    return im


def t_anthracite_ore(n):
    return ore(n, stone(n + "b", (126, 126, 126), 10), (28, 30, 44), 8, (86, 92, 120))


def t_deepslate_anthracite(n):
    return ore(n, deepslate(n + "b"), (30, 32, 48), 8, (96, 104, 134))


def t_anthracite_block(n):
    im = noise(n, (36, 38, 46, 255), 8)
    r = rng(n + "s")
    for _ in range(20):
        im.putpixel((r.randrange(S), r.randrange(S)), (96, 104, 128, 255))
    for i in range(S):
        im.putpixel((i, 15), (20, 20, 26, 255))
        im.putpixel((15, i), (20, 20, 26, 255))
    return im


def t_coke_block(n):
    im = noise(n, (112, 112, 118, 255), 14)
    r = rng(n + "p")
    for _ in range(14):
        x, y = r.randint(1, 14), r.randint(1, 14)
        im.putpixel((x, y), (60, 60, 66, 255))
        im.putpixel((x + 1 if x < 15 else x, y), (66, 66, 72, 255))
    return im


def t_bunker(n):
    im = noise(n, (92, 98, 108, 255), 5)
    for y in range(S):
        for x in range(S):
            if y in (0, 1) or x in (0, 15) or y == 15:
                im.putpixel((x, y), (60, 64, 72, 255))
            elif 4 <= y <= 12 and 3 <= x <= 12:
                im.putpixel((x, y), shade((26, 26, 30, 255), rng(f"{n}{x}{y}").randint(-6, 10)))
    for p in ((2, 14), (13, 14)):
        im.putpixel(p, (150, 150, 158, 255))
    return im


def t_timber_side(n):
    im = new()
    for y in range(S):
        for x in range(S):
            base = (96, 66, 38) if (x // 2) % 2 == 0 else (88, 60, 34)
            im.putpixel((x, y), shade(base + (255,), rng(f"{n}{x}{y}").randint(-6, 6)))
    for x in (0, 15):
        for y in range(S):
            im.putpixel((x, y), (66, 44, 24, 255))
    return im


def t_timber_end(n):
    im = new((120, 88, 52, 255))
    for ring in (2, 4, 6):
        for a in range(S):
            for b in range(S):
                if max(abs(a - 7.5), abs(b - 7.5)) == ring + 0.5:
                    im.putpixel((a, b), (96, 66, 38, 255))
    for x in range(S):
        for y in range(S):
            if x in (0, 15) or y in (0, 15):
                im.putpixel((x, y), (74, 50, 28, 255))
    return im


def t_timber_planks(n):
    im = new()
    for y in range(S):
        plank = y // 4
        for x in range(S):
            base = [(110, 80, 46), (102, 74, 42), (116, 84, 50), (98, 70, 40)][plank]
            c = shade(base + (255,), rng(f"{n}{x}{y}").randint(-5, 5))
            if y % 4 == 3:
                c = shade(c, -26)
            im.putpixel((x, y), c)
    for p in ((2, 1), (13, 5), (3, 9), (12, 13)):
        im.putpixel(p, (58, 44, 32, 255))
    return im


def t_lamp(n):
    im = new((40, 40, 44, 255))
    for y in range(2, 14):
        for x in range(2, 14):
            d = abs(x - 7.5) + abs(y - 7.5)
            c = (255, 240, 170) if d < 5 else (252, 206, 96)
            im.putpixel((x, y), c + (255,))
    for i in range(S):
        im.putpixel((i, 0), (70, 70, 76, 255))
        im.putpixel((i, 15), (70, 70, 76, 255))
        im.putpixel((0, i), (70, 70, 76, 255))
        im.putpixel((15, i), (70, 70, 76, 255))
    for i in (5, 10):
        for j in range(2, 14):
            im.putpixel((i, j), (90, 82, 56, 255))
            im.putpixel((j, i), (90, 82, 56, 255))
    return im


def t_vent(n):
    im = new((54, 56, 62, 255))
    for y in range(2, 14, 3):
        for x in range(1, 15):
            im.putpixel((x, y), (140, 144, 152, 255))
            im.putpixel((x, y + 1), (96, 100, 108, 255))
    for p in ((0, 0), (15, 0), (0, 15), (15, 15)):
        im.putpixel(p, (170, 172, 180, 255))
    return im


def t_ballast(n):
    r = rng(n)
    im = new()
    for y in range(S):
        for x in range(S):
            v = r.choice([70, 84, 100, 116, 132, 62])
            im.putpixel((x, y), (v, v - 2, v - 6, 255))
    return im


def t_sleepers_side(n):
    im = new()
    for y in range(S):
        for x in range(S):
            base = (74, 54, 40) if (y // 3) % 2 == 0 else (66, 48, 36)
            im.putpixel((x, y), shade(base + (255,), rng(f"{n}{x}{y}").randint(-6, 6)))
    for x in range(S):
        im.putpixel((x, 0), (40, 30, 24, 255))
        im.putpixel((x, 15), (40, 30, 24, 255))
    return im


def t_sleepers_end(n):
    im = new((90, 66, 48, 255))
    for x in range(S):
        for y in range(S):
            if x in (0, 15) or y in (0, 15):
                im.putpixel((x, y), (46, 34, 26, 255))
            elif (x + y) % 5 == 0:
                im.putpixel((x, y), (70, 50, 38, 255))
    return im


def t_wagon(n):
    im = new()
    for y in range(S):
        for x in range(S):
            base = (128, 56, 44) if x % 4 in (0, 1) else (112, 46, 36)
            c = shade(base + (255,), rng(f"{n}{x}{y}").randint(-6, 6))
            im.putpixel((x, y), c)
    for y in (0, 15):
        for x in range(S):
            im.putpixel((x, y), (60, 26, 22, 255))
    r = rng(n + "s")
    for _ in range(10):
        im.putpixel((r.randrange(S), r.randrange(S)), (170, 110, 70, 255))
    return im


BLOCK_TEXTURES = {
    "mine_concrete": t_mine_concrete, "reinforced_mine_concrete": t_reinforced,
    "cracked_mine_concrete": t_cracked, "soot_stained_concrete": t_soot,
    "slag_block": t_slag_block, "slag_bricks": t_slag_bricks, "polished_slag": t_polished_slag,
    "sooty_bricks": t_sooty_bricks, "whitewashed_wall": t_whitewash, "clay_plaster": t_clay_plaster,
    "prefab_panel": t_prefab, "slate_roof": t_slate, "rusty_iron_block": t_rusty_iron,
    "rusty_plate": t_rusty_plate, "factory_glass": t_factory_glass, "rusty_fence": t_rusty_fence,
    "chimney_bricks": t_chimney, "hazard_stripes": t_hazard,
    "steel_girder_side": t_girder_side, "steel_girder_end": t_girder_end,
    "spoil_rock": t_spoil_rock, "burnt_spoil": t_burnt_spoil, "spoil_gravel": t_spoil_gravel,
    "coal_shale": t_coal_shale, "smoldering_spoil": t_smoldering,
    "coal_seam": t_coal_seam, "anthracite_ore": t_anthracite_ore,
    "deepslate_anthracite_ore": t_deepslate_anthracite, "anthracite_block": t_anthracite_block,
    "coke_block": t_coke_block, "coal_bunker": t_bunker,
    "mine_timber_beam_side": t_timber_side, "mine_timber_beam_end": t_timber_end,
    "mine_timber_planks": t_timber_planks, "mine_lamp": t_lamp, "ventilation_grate": t_vent,
    "railway_ballast": t_ballast, "rail_sleepers_side": t_sleepers_side,
    "rail_sleepers_end": t_sleepers_end, "freight_wagon_plating": t_wagon,
}


# ------------------------------------------------------------- item art -----
def lump(name, base, hi, lo, pts):
    """Draw a chunky lump from (x, y) points with simple top-left lighting."""
    im = new()
    r = rng(name)
    pset = set(pts)
    for (x, y) in pts:
        c = base
        if (x - 1, y) not in pset or (x, y - 1) not in pset:
            c = hi
        if (x + 1, y) not in pset or (x, y + 1) not in pset:
            c = lo
        im.putpixel((x, y), shade(c + (255,), r.randint(-4, 4)))
    return im


def blob(cx, cy, rx, ry, seed):
    r = random.Random(seed)
    pts = []
    for y in range(S):
        for x in range(S):
            d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
            if d < 1.0 + r.uniform(-0.25, 0.15):
                pts.append((x, y))
    return pts


def i_anthracite(n):
    im = lump(n, (40, 42, 54), (92, 100, 128), (20, 20, 28), blob(7.5, 8, 5.5, 4.8, 11))
    return im


def i_coke(n):
    im = lump(n, (118, 118, 124), (168, 168, 176), (70, 70, 76), blob(7.5, 8, 5.4, 4.6, 5))
    for p in ((6, 7), (9, 9), (7, 10)):
        if im.getpixel(p)[3]:
            im.putpixel(p, (54, 54, 60, 255))
    return im


def i_coal_dust(n):
    im = new()
    r = rng(n)
    for y in range(6, 14):
        w = (y - 5)
        for x in range(8 - w, 8 + w):
            if 0 <= x < S and r.random() < 0.8:
                v = r.randint(18, 52)
                im.putpixel((x, y), (v, v, v + 4, 255))
    return im


def i_slag(n):
    im = lump(n, (110, 112, 118), (156, 158, 166), (66, 68, 74), blob(7.5, 8, 5.2, 4.4, 23))
    for p in ((5, 8), (9, 7), (8, 11)):
        if im.getpixel(p)[3]:
            im.putpixel(p, (40, 42, 48, 255))
    return im


def i_scrap(n):
    im = new()
    r = rng(n)
    shapes = [((2, 3), (7, 5)), ((6, 8), (13, 10)), ((3, 11), (8, 13)), ((10, 2), (13, 6))]
    for (x0, y0), (x1, y1) in shapes:
        for y in range(y0, y1):
            for x in range(x0, x1):
                c = (132, 136, 144) if (x + y) % 3 else (150, 90, 58)
                im.putpixel((x, y), shade(c + (255,), r.randint(-8, 8)))
        for x in range(x0, x1):
            im.putpixel((x, y1 - 1), (74, 76, 84, 255))
    return im


def i_gear(n):
    im = new()
    cx = cy = 7.5
    for y in range(S):
        for x in range(S):
            d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            ang = (x - cx, y - cy)
            tooth = (abs(x - cx) < 1.6 or abs(y - cy) < 1.6 or abs(abs(x - cx) - abs(y - cy)) < 1.2) and d < 7.6
            if d < 5.4 or tooth:
                if d < 2.0:
                    continue
                c = (156, 92, 56) if d > 3.5 else (118, 66, 40)
                im.putpixel((x, y), shade(c + (255,), rng(f"{n}{x}{y}").randint(-10, 10)))
    return im


def i_token(n):
    im = new()
    for y in range(S):
        for x in range(S):
            d = ((x - 7.5) / 6.0) ** 2 + ((y - 7.5) / 5.0) ** 2
            if d < 1.0:
                c = (210, 170, 70) if d > 0.55 else (236, 202, 104)
                im.putpixel((x, y), c + (255,))
    for y in (7, 8):
        for x in range(5, 11):
            im.putpixel((x, y), (96, 70, 24, 255))
    for p in ((7, 5), (8, 5), (7, 10), (8, 10)):
        im.putpixel(p, (96, 70, 24, 255))
    im.putpixel((7, 2), (60, 44, 20, 255))
    return im


def i_ration(n):
    im = new()
    for y in range(4, 13):
        for x in range(2, 14):
            edge = y in (4, 12) or x in (2, 13)
            c = (150, 100, 52) if edge else (204, 150, 84)
            im.putpixel((x, y), shade(c + (255,), rng(f"{n}{x}{y}").randint(-6, 6)))
    for x in range(3, 13):
        im.putpixel((x, 8), (176, 60, 52, 255))
    for p in ((4, 6), (8, 6), (11, 10), (5, 10)):
        im.putpixel(p, (236, 196, 120, 255))
    return im


def i_ticket(n):
    im = new()
    for y in range(3, 13):
        for x in range(1, 15):
            c = (236, 226, 190) if (x + y) % 7 else (228, 216, 176)
            im.putpixel((x, y), c + (255,))
    for x in range(1, 15):
        im.putpixel((x, 3), (160, 40, 36, 255))
        im.putpixel((x, 12), (160, 40, 36, 255))
    for y in range(3, 13):
        im.putpixel((1, y), (160, 40, 36, 255))
        im.putpixel((14, y), (160, 40, 36, 255))
    for x in range(3, 8):
        im.putpixel((x, 6), (60, 56, 50, 255))
        im.putpixel((x, 8), (60, 56, 50, 255))
    for x in range(3, 11):
        im.putpixel((x, 10), (90, 86, 80, 255))
    for p in ((11, 6), (12, 6), (11, 7), (12, 7)):
        im.putpixel(p, (30, 30, 34, 255))
    return im


def i_pickaxe(n):
    """Miner's pickaxe: wooden handle, dark steel head with a coke-black tint."""
    im = new()
    for i in range(10):                                   # handle from bottom-left to the head
        x, y = 2 + i, 13 - i
        im.putpixel((x, y), (116, 82, 44, 255))
        if i % 3 == 1:
            im.putpixel((x, y), (96, 66, 34, 255))
    head = [(3, 7), (4, 6), (5, 5), (6, 4), (7, 3), (8, 3), (9, 3), (10, 3), (11, 4), (12, 5), (13, 6), (13, 7)]
    for k, (x, y) in enumerate(head):
        im.putpixel((x, y), (92, 98, 112, 255))
        if (x, y - 1) in head or (x - 1, y) in head:
            pass
    for (x, y) in head[1:-1]:                             # thicken the head towards the handle
        if 0 <= y + 1 < S and im.getpixel((x, y + 1))[3] == 0 and y + 1 <= 6:
            im.putpixel((x, y + 1), (66, 70, 82, 255))
    for (x, y) in ((6, 4), (7, 3), (8, 3), (9, 3)):       # highlight on the top edge
        im.putpixel((x, y), (150, 158, 176, 255))
    for (x, y) in ((3, 7), (13, 7)):                      # dark pick tips
        im.putpixel((x, y), (40, 42, 50, 255))
    return im


ITEM_TEXTURES = {
    "anthracite": i_anthracite, "coke": i_coke, "coal_dust": i_coal_dust, "slag": i_slag,
    "iron_scrap": i_scrap, "rusty_gear": i_gear, "miners_token": i_token,
    "miners_ration": i_ration, "donbass_ticket": i_ticket,
    "miners_pickaxe": i_pickaxe,
}


def main():
    for name, fn in BLOCK_TEXTURES.items():
        save(fn(name), BLOCK_DIR, name)
    for name, fn in ITEM_TEXTURES.items():
        save(fn(name), ITEM_DIR, name)
    print(f"textures: {len(BLOCK_TEXTURES)} block, {len(ITEM_TEXTURES)} item")
    import gen_textures_gear
    gen_textures_gear.main()


if __name__ == "__main__":
    main()

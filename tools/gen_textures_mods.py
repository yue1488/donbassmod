"""Textures of the 0.3.0 weapon workbench (block faces) and the five AK modification kits (item icons).

Every kit icon is a small riveted steel board with the part drawn on it and a colour-coded top edge, so that the five
kits can be told apart in a hotbar at a glance:  magazine = brass, mechanism = red, stabilizer = blue,
barrel = orange, spring = green.
"""
import math

from PIL import Image

from gen_textures import BLOCK_DIR, ITEM_DIR, S, clamp, new, noise, rng, save, shade

BOARD = (64, 68, 78, 255)
BOARD_HI = (98, 104, 118, 255)
BOARD_LO = (36, 38, 46, 255)
RIVET = (170, 176, 190, 255)
EDGE = {"magazine": (214, 168, 70, 255), "mechanism": (200, 56, 48, 255), "stabilizer": (70, 130, 210, 255),
        "barrel": (222, 128, 52, 255), "spring": (84, 184, 92, 255)}


# ---------------------------------------------------------------- block faces ----
def t_workbench_top(n):
    """Steel work surface: brushed plate, a vise-slot, a few tool marks and bolts."""
    im = noise(n, (96, 102, 114, 255), 5)
    for y in range(S):                                              # brushed horizontal grain
        for x in range(S):
            if (x + 3 * y) % 5 == 0:
                im.putpixel((x, y), shade(im.getpixel((x, y)), 7))
    for i in range(S):                                              # dark frame
        for p in ((i, 0), (i, 15), (0, i), (15, i)):
            im.putpixel(p, (44, 46, 54, 255))
        for p in ((i, 1), (1, i)):
            if 1 <= i <= 14:
                im.putpixel(p, (132, 138, 152, 255))
    for x in range(3, 8):                                           # the vise slot
        for y in (4, 5):
            im.putpixel((x, y), (30, 32, 38, 255))
    for x in range(3, 8):
        im.putpixel((x, 6), (140, 146, 160, 255))
    for (x, y) in ((10, 9), (11, 9), (12, 9), (11, 10), (11, 11), (11, 12)):      # a wrench-like mark
        im.putpixel((x, y), (58, 62, 72, 255))
    for (x, y) in ((2, 2), (13, 2), (2, 13), (13, 13)):             # corner bolts
        im.putpixel((x, y), RIVET)
        im.putpixel((x + 1 if x < 8 else x - 1, y), (60, 64, 74, 255))
    for (x, y) in ((5, 11), (6, 12), (8, 12)):                      # oil spots
        im.putpixel((x, y), (52, 50, 46, 255))
    return im


def t_workbench_side(n):
    """Painted steel cabinet: a dark apron on top, a drawer with a handle, a hazard-yellow edge strip."""
    im = noise(n, (84, 90, 100, 255), 5)
    for x in range(S):                                              # top apron
        for y in (0, 1, 2):
            im.putpixel((x, y), shade((58, 62, 72, 255), -(2 - y) * 4))
        im.putpixel((x, 3), (130, 136, 150, 255))
    for y in range(4, 15):                                          # drawer outline
        for x in (2, 13):
            im.putpixel((x, y), (46, 50, 58, 255))
    for x in range(2, 14):
        for y in (4, 14):
            im.putpixel((x, y), (46, 50, 58, 255))
    for x in range(3, 13):
        im.putpixel((x, 5), (122, 128, 142, 255))
    for x in range(6, 10):                                          # the handle
        im.putpixel((x, 8), (176, 182, 196, 255))
        im.putpixel((x, 9), (60, 64, 74, 255))
    for x in range(S):                                              # hazard strip at the very bottom
        im.putpixel((x, 15), (220, 180, 40, 255) if (x // 2) % 2 == 0 else (36, 36, 40, 255))
    for (x, y) in ((3, 6), (12, 6), (3, 12), (12, 12)):
        im.putpixel((x, y), RIVET)
    return im


# ------------------------------------------------------------------ item icons ----
def board(kind):
    """The common backing: steel plate with rivets and a coloured top edge."""
    im = new()
    r = rng("mod_board_" + kind)
    for y in range(2, 14):
        for x in range(1, 15):
            c = BOARD
            if y == 2 or x == 1:
                c = BOARD_HI
            elif y == 13 or x == 14:
                c = BOARD_LO
            im.putpixel((x, y), shade(c, r.randint(-3, 3)))
    for x in range(1, 15):
        im.putpixel((x, 2), EDGE[kind])
        im.putpixel((x, 3), shade(EDGE[kind], -48))
    for p in ((2, 12), (13, 12)):
        im.putpixel(p, RIVET)
    return im


def i_magazine_kit(n):
    im = board("magazine")
    # a long curved magazine drawn from the top-left to the bottom-right, with a column of rounds visible
    pts = [(5, 4), (5, 5), (6, 6), (6, 7), (7, 8), (7, 9), (8, 10), (8, 11)]
    for i, (x, y) in enumerate(pts):
        for dx in range(0, 5):
            col = (36, 38, 46, 255) if dx in (0, 4) else (112, 118, 134, 255)
            if dx == 1:
                col = (150, 158, 174, 255)
            im.putpixel((x + dx, y), shade(col, -(i * 2)))
    for y in (4, 5):                                                # brass rounds peeking out of the top
        for x in (6, 8):
            im.putpixel((x, y), (222, 176, 76, 255))
    for x in range(5, 10):                                          # extended floor plate (the +50 % part)
        im.putpixel((x + 3, 12), (214, 168, 70, 255))
    return im


def i_mechanism_kit(n):
    im = board("mechanism")
    for (cx, cy, rad) in ((6, 7, 3.2), (10, 10, 2.4)):             # two gears
        for y in range(S):
            for x in range(S):
                d = math.hypot(x - cx, y - cy)
                tooth = (abs(x - cx) < 0.9 or abs(y - cy) < 0.9) and d < rad + 1.3
                if (rad - 1.0 < d <= rad + 0.2 or tooth) and d > 0.9 and 4 <= y <= 12 and 2 <= x <= 13:
                    im.putpixel((x, y), shade((188, 194, 208, 255), -int(d * 4)))
    for p in ((10, 4), (11, 4), (10, 5), (11, 5)):                  # a redstone dot: "faster reload"
        im.putpixel(p, (214, 40, 36, 255))
    im.putpixel((10, 4), (255, 120, 100, 255))
    return im


def i_stabilizer_kit(n):
    im = board("stabilizer")
    for y in range(6, 11):                                          # a slotted muzzle device (horizontal cylinder)
        for x in range(3, 13):
            c = (118, 124, 140, 255) if y in (7, 8) else (74, 78, 92, 255)
            if y == 6:
                c = (156, 164, 180, 255)
            if y == 10:
                c = (40, 42, 50, 255)
            im.putpixel((x, y), c)
    for x in (5, 7, 9):                                             # vent slots
        for y in (6, 7):
            im.putpixel((x, y), (26, 28, 34, 255))
    for y in range(7, 10):                                          # bore at the left end
        im.putpixel((3, y), (14, 14, 18, 255))
    for x in range(10, 13):                                         # threaded end
        im.putpixel((x, 8), (190, 196, 210, 255))
    return im


def i_barrel_kit(n):
    im = board("barrel")
    for i in range(0, 11):                                          # a thick barrel on the diagonal
        x, y = 2 + i, 11 - i
        for t in range(-1, 2):
            px, py = x + t, y
            if 2 <= px <= 13 and 4 <= py <= 12:
                im.putpixel((px, py), (176, 182, 196, 255) if t == -1 else
                            ((110, 116, 130, 255) if t == 0 else (50, 54, 64, 255)))
    for (x, y) in ((12, 4), (11, 4), (12, 5), (13, 4)):             # muzzle crown
        im.putpixel((x, y), (30, 32, 38, 255))
    for (x, y) in ((4, 9), (5, 8), (7, 6)):                         # reinforcing rings
        im.putpixel((x, y), (230, 140, 60, 255))
        im.putpixel((x + 1, y), (230, 140, 60, 255))
    return im


def i_spring_kit(n):
    im = board("spring")
    ys = [5 + abs(((x - 3) % 4) - 2) * 3 for x in range(3, 13)]     # a coil spring seen from the side: a triangle wave
    for i, x in enumerate(range(3, 13)):
        y = ys[i]
        lo, hi = (min(y, ys[i - 1]), max(y, ys[i - 1])) if i else (y, y)
        for yy in range(lo, hi + 1):                                # join the turns so that the coil reads as one wire
            falling = i and ys[i] > ys[i - 1]
            im.putpixel((x, yy), (196, 202, 216, 255) if falling else (112, 118, 134, 255))
        im.putpixel((x, y), (236, 240, 248, 255) if y == 5 else (84, 90, 104, 255))
    for y in range(5, 12):                                          # end caps
        im.putpixel((2, y), (150, 156, 170, 255))
        im.putpixel((13, y), (150, 156, 170, 255))
    return im


BLOCKS = {"weapon_workbench_top": t_workbench_top, "weapon_workbench_side": t_workbench_side}
ITEMS = {"ak_mod_magazine": i_magazine_kit, "ak_mod_mechanism": i_mechanism_kit, "ak_mod_stabilizer": i_stabilizer_kit,
         "ak_mod_barrel": i_barrel_kit, "ak_mod_spring": i_spring_kit}


def main():
    for name, fn in BLOCKS.items():
        save(fn(name), BLOCK_DIR, name)
    for name, fn in ITEMS.items():
        save(fn(name), ITEM_DIR, name)
    print(f"mod/workbench textures: {len(BLOCKS)} block, {len(ITEMS)} item")


if __name__ == "__main__":
    main()

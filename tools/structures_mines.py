"""Mine complexes: surface headframe/shed + vertical shaft + underground levels.

Template layout (footprint 21 x 21, shaft centre at x=10, z=10):
  y = 0 .. G-1   underground (shaft lining, galleries carved into the rock)
  y = G          ground layer (yard); the structure's start_height is -G so this layer
                 lands on the terrain surface
  y > G          buildings / headframe
Returns {name: (Tpl, ground_y, loot_summary)}.
"""
import random
import zlib

from nbt import Tpl

M = "donbass:"
SIZE = 21
C = 10  # centre


def seeded(name):
    return random.Random(zlib.crc32(name.encode()))


def shaft(t, G, ladders=True):
    """5x5 shaft (x,z 8..12) lined with timber (ring 7..13), from y=0 up to the ground layer."""
    for y in range(0, G + 1):
        for x in range(7, 14):
            for z in range(7, 14):
                ring = x in (7, 13) or z in (7, 13)
                if y == 0:
                    t.set(x, y, z, M + "mine_concrete")
                elif ring:
                    t.set(x, y, z, M + ("mine_concrete" if y == G else "mine_timber_planks"))
                else:
                    t.set(x, y, z, "minecraft:air")
    if ladders:
        # Ladders need a supporting block; the lining only reaches the ground layer (y=G).
        t.ladder(8, 1, G, 8, "east")      # attached to the lining block at x=7
        t.ladder(12, 1, G, 12, "west")    # attached to the lining block at x=13


def yard(t, G, rng, height_clear=6):
    """Foundation skirt + gravel/dirt yard + cleared air above, so the pad sits flat on the steppe."""
    for x in range(SIZE):
        for z in range(SIZE):
            t.set(x, G - 2, z, "minecraft:dirt")
            t.set(x, G - 1, z, "minecraft:coarse_dirt")
            t.set(x, G, z, rng.choice(["minecraft:coarse_dirt", "minecraft:gravel", M + "railway_ballast",
                                       M + "railway_ballast", M + "spoil_gravel"]))
    t.air(0, G + 1, 0, SIZE - 1, G + height_clear, SIZE - 1)


def fence(t, G, gap=(9, 11)):
    """Perimeter fence with a gate gap in the middle of the south side (z = SIZE-1)."""
    for i in range(SIZE):
        for (x, z) in ((i, 0), (i, SIZE - 1), (0, i), (SIZE - 1, i)):
            if z == SIZE - 1 and gap[0] <= x <= gap[1]:
                continue
            t.set(x, G + 1, z, M + "rusty_fence")


def headframe(t, G, H, rng, support="minecraft:iron_bars"):
    """Steel headframe (kopyor): four legs, ring braces and a hoisting wheel over the shaft."""
    legs = [(5, 5), (15, 5), (5, 15), (15, 15)]
    top = G + H
    for (x, z) in legs:
        t.pillar(x, G + 1, top, z, M + "steel_girder")
    for y in (G + H // 2, top):
        for i in range(5, 16):
            t.set(i, y, 5, M + "steel_girder", {"axis": "x"})
            t.set(i, y, 15, M + "steel_girder", {"axis": "x"})
        for i in range(6, 15):
            t.set(5, y, i, M + "steel_girder", {"axis": "z"})
            t.set(15, y, i, M + "steel_girder", {"axis": "z"})
    # hoisting wheel in the Y-Z plane above the shaft, with hub and axle
    cy = top - 3
    t.wheel(C, cy, C, 3, "minecraft:iron_bars")
    t.set(C, cy, C, "minecraft:iron_block")
    for x in range(5, 16):
        if x != C:
            t.set(x, cy, C, M + "rusty_iron_block")
    # hoisting rope down into the shaft
    for y in range(G - 6, cy):
        t.set(C, y, C, "minecraft:chain", {"axis": "y", "waterlogged": "false"})
    t.set(C, G - 7, C, "minecraft:lantern", {"hanging": "true", "waterlogged": "false"})
    # braces down the middle of each side
    for y in range(G + 2, top, 2):
        t.set(10, y, 5, M + "rusty_fence")
        t.set(10, y, 15, M + "rusty_fence")


def shed(t, G):
    """Small timber headgear shed over a shallow shaft."""
    for (x, z) in ((6, 6), (14, 6), (6, 14), (14, 14)):
        t.pillar(x, G + 1, G + 4, z, M + "mine_timber_beam")
    for x in range(5, 16):
        for z in range(5, 16):
            t.set(x, G + 5, z, M + "mine_timber_planks")
    for x in range(5, 16):
        for z in (5, 15):
            t.set(x, G + 6, z, M + "mine_timber_planks")
    # clear the space under the roof first, then hang the lamp (order matters: air overwrites)
    t.air(7, G + 1, 7, 13, G + 4, 13)
    t.set(C, G + 4, C, "minecraft:chain", {"axis": "y", "waterlogged": "false"})
    t.set(C, G + 3, C, "minecraft:lantern", {"hanging": "true", "waterlogged": "false"})


def engine_house(t, G, rng, loot):
    t.walls(15, G + 1, 7, 19, G + 4, 13, M + "slag_bricks")
    t.fill(15, G, 7, 19, G, 13, M + "mine_concrete")
    t.fill(15, G + 5, 7, 19, G + 5, 13, M + "slate_roof")
    t.air(16, G + 1, 8, 18, G + 4, 12)
    for z in (9, 11):
        t.set(15, G + 3, z, M + "factory_glass")
        t.set(19, G + 3, z, M + "factory_glass")
    t.door(15, G + 1, 10, "west", "minecraft:iron_door")
    t.set(17, G + 4, 10, M + "mine_lamp")
    t.set(18, G + 1, 8, M + "coal_bunker")
    t.set(18, G + 1, 12, M + "coal_bunker")
    t.chest(16, G + 1, 12, "west", M + "chests/" + loot)
    # chimney
    for y in range(G + 6, G + 12):
        t.set(18, y, 8, M + "chimney_bricks")


def levels(t, G, ys, rng, support, lamps, webs, spawners, loots):
    """Cross-shaped galleries at each level in ys (floor y), with rails, supports and chests."""
    for idx, ly in enumerate(ys):
        # carve the galleries (3 wide, 3 high) and open the shaft lining at this level
        for z in range(9, 12):
            t.air(1, ly + 1, z, 6, ly + 3, z)
            t.air(14, ly + 1, z, 19, ly + 3, z)
            t.air(7, ly + 1, z, 7, ly + 3, z)
            t.air(13, ly + 1, z, 13, ly + 3, z)
        for x in range(9, 12):
            t.air(x, ly + 1, 1, x, ly + 3, 6)
            t.air(x, ly + 1, 14, x, ly + 3, 19)
            t.air(x, ly + 1, 7, x, ly + 3, 7)
            t.air(x, ly + 1, 13, x, ly + 3, 13)
        # rails along the gallery centre lines
        for x in list(range(1, 7)) + list(range(14, 20)):
            t.rail(x, ly + 1, C, "east_west")
        for z in list(range(1, 7)) + list(range(14, 20)):
            t.rail(C, ly + 1, z, "north_south")
        # supports every 4 blocks
        beam = M + ("reinforced_mine_concrete" if support == "concrete" else "mine_timber_planks")
        post = M + ("reinforced_mine_concrete" if support == "concrete" else "mine_timber_beam")
        for k in (2, 5, 15, 18):
            for (px, pz) in ((k, 9), (k, 11)):                    # east-west drifts
                t.set(px, ly + 1, pz, post)
                t.set(px, ly + 2, pz, post)
            for z in (9, 10, 11):
                t.set(k, ly + 3, z, beam)
            for (px, pz) in ((9, k), (11, k)):                    # north-south drifts
                t.set(px, ly + 1, pz, post)
                t.set(px, ly + 2, pz, post)
            for x in (9, 10, 11):
                t.set(x, ly + 3, k, beam)
            if lamps:
                t.set(k, ly + 3, 10, M + "mine_lamp")
                t.set(10, ly + 3, k, M + "mine_lamp")
        # decay: cobwebs
        if webs:
            for x in list(range(1, 7)) + list(range(14, 20)):
                for z in (9, 10, 11):
                    for y in (ly + 2, ly + 3):
                        if rng.random() < webs * 0.35:
                            t.set(x, y, z, "minecraft:cobweb")
        # end rooms: east end chest alcove, west end spawner alcove
        t.air(17, ly + 1, 8, 19, ly + 3, 12)
        loot = loots[idx % len(loots)]
        t.chest(19, ly + 1, C, "west", M + "chests/" + loot)
        if idx % 2 == 0 and loot != "mine_deep":
            t.chest(19, ly + 1, 12, "west", M + "chests/mine_shallow")
        if spawners:
            ent = spawners[min(idx, len(spawners) - 1)]
            t.air(1, ly + 1, 8, 3, ly + 3, 12)
            t.spawner(1, ly + 1, C, ent)
            t.set(2, ly + 1, 9, "minecraft:cobweb")
            t.set(2, ly + 1, 11, "minecraft:cobweb")
            t.chest(2, ly + 1, 12, "north", M + "chests/" + loots[0])
        # bottom of each level gets lanterns near the shaft so the junction is visible
        if lamps:
            t.set(8, ly + 3, 8, M + "mine_lamp")
            t.set(12, ly + 3, 12, M + "mine_lamp")


CFG = {
    # name: (G, levels_floor_y, support, surface, H, lamps, cobweb, spawners, chest loot per level, processors)
    "mine_shallow": dict(G=14, ys=[4], support="timber", surface="shed", H=0, lamps=False, webs=0.5,
                         spawners=None, loots=["mine_shallow"]),
    "mine_active": dict(G=24, ys=[15, 6], support="concrete", surface="frame", H=14, lamps=True, webs=0.0,
                        spawners=None, loots=["mine_active", "mine_active"]),
    "mine_deep": dict(G=44, ys=[34, 21, 7], support="timber", surface="frame", H=14, lamps=False, webs=0.9,
                      spawners=["minecraft:cave_spider", "minecraft:zombie", "minecraft:skeleton"],
                      loots=["mine_shallow", "mine_active", "mine_deep"]),
}


def build(name):
    c = CFG[name]
    G = c["G"]
    t = Tpl(SIZE, G + 1 + max(c["H"], 7) + 6, SIZE)
    rng = seeded(name)
    yard(t, G, rng)
    shaft(t, G)
    levels(t, G, c["ys"], rng, c["support"], c["lamps"], c["webs"], c["spawners"], c["loots"])
    if c["surface"] == "frame":
        headframe(t, G, c["H"], rng)
        engine_house(t, G, rng, c["loots"][0] if c["loots"][0] != "mine_shallow" else "mine_active")
        fence(t, G)
        # ore wagon on a short surface track next to the shaft
        for x in range(1, 5):
            t.rail(x, G + 1, 2, "east_west")
    else:
        shed(t, G)
        fence(t, G)
        t.chest(16, G + 1, 4, "south", M + "chests/mine_shallow")
        t.set(4, G + 1, 16, "minecraft:barrel", {"facing": "up", "open": "false"})
    return t, G


def all_templates():
    out = {}
    for name in CFG:
        t, G = build(name)
        out["mine/" + name.replace("mine_", "")] = (t, G)
    return out

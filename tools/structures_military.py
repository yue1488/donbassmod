"""Fortified checkpoints ("blockposts") of the two fictional squads, one 17 x 14 x 17 template each.

Layout (x east, z south; y = 1 is the ground layer, the yard lands on the terrain surface):
  perimeter wall with a gate in the south side, barracks (north-west), covered stores (south-west),
  campfire with seats in the middle, flag pole, watchtower (south-east corner, ladder inside).
The squad only changes colours, the flag and the loot tables of the chests.

Flags (0.4.0): the checkpoint of the DPR squad ("north", steppe uniform, "Ополченец ДНР") flies the DPR flag, the one of the
LPR squad ("south", terricone uniform, "Ополченец ЛНР") the LPR flag - one flag per checkpoint, never both.  A flag is
four wool blocks wide and three high, built into the template (so it is generated together with the structure), on a
12-block girder pole that is much taller than the walls (the walls are 2 high, the tower 9) and therefore visible from
afar.  Stripes top to bottom: DPR black / blue / red, LPR light blue / blue / red (both 2:3 horizontal tricolours).
"""
import random
import zlib

from nbt import Byte, Tpl
from populate import fighter_nbt

M = "donbass:"
SIZE = 17
H = 14
G = 1

# the flags, stripes from the top down (plain wool blocks; no mechanics)
FLAG_DPR = ("minecraft:black_wool", "minecraft:blue_wool", "minecraft:red_wool")
FLAG_LPR = ("minecraft:light_blue_wool", "minecraft:blue_wool", "minecraft:red_wool")
# the pole stands in the yard (x = 11, z = 4); the flag hangs east of it, its top row is the top row of the template
POLE_X, POLE_Z = 11, 4
FLAG_X0, FLAG_X1 = POLE_X + 1, POLE_X + 4

SQUADS = {
    # faction id -> (flag stripes top to bottom, bed colour, wall block)
    "north": (FLAG_DPR, "gray", M + "whitewashed_wall"),
    "south": (FLAG_LPR, "orange", M + "sooty_bricks"),
}


def build(faction):
    flag, bed_color, wall = SQUADS[faction]
    rng = random.Random(zlib.crc32(("blockpost_" + faction).encode()))
    t = Tpl(SIZE, H, SIZE)

    # ---- yard on top of a foundation, then clear the air above it
    for x in range(SIZE):
        for z in range(SIZE):
            t.set(x, 0, z, "minecraft:coarse_dirt")
            t.set(x, 1, z, rng.choice(["minecraft:coarse_dirt", "minecraft:gravel", M + "railway_ballast",
                                       M + "spoil_gravel"]))
    t.air(0, 2, 0, SIZE - 1, H - 1, SIZE - 1)

    # ---- perimeter wall (2 high) with a 3-wide gate in the middle of the south side
    for i in range(1, 16):
        for (x, z) in ((i, 1), (i, 15), (1, i), (15, i)):
            if z == 15 and 7 <= x <= 9:
                continue
            for y in (2, 3):
                t.set(x, y, z, M + "slag_bricks" if (x + z + y) % 5 else M + "slag_block")
    # gate posts and a hazard-striped lintel
    for x in (6, 10):
        t.pillar(x, 2, 4, 15, M + "steel_girder")
    t.fill(6, 5, 15, 10, 5, 15, M + "hazard_stripes")
    # cover blocks inside the gate (a chicane) and a few sandbag-like stacks
    for (x, z) in ((5, 12), (6, 12), (10, 12), (11, 12), (4, 9), (12, 6)):
        t.set(x, 2, z, M + "slag_block")
    t.set(5, 3, 12, M + "slag_block")
    t.set(11, 3, 12, M + "slag_block")

    # ---- barracks (x 2..8, z 2..7): planks floor, panel walls, slate roof
    t.fill(2, 2, 2, 8, 2, 7, "minecraft:spruce_planks")
    t.walls(2, 3, 2, 8, 5, 7, wall)
    t.fill(2, 6, 2, 8, 6, 7, M + "slate_roof")
    t.fill(3, 7, 3, 7, 7, 6, M + "slate_roof")
    t.air(3, 3, 3, 7, 5, 6)
    t.door(5, 3, 7, "south", "minecraft:spruce_door")
    for (x, z) in ((3, 2), (7, 2), (2, 4), (8, 4)):                       # windows
        t.set(x, 4, z, M + "factory_glass")
    t.bed(3, 3, 3, "south", bed_color)
    t.bed(5, 3, 3, "south", bed_color)
    t.chest(7, 3, 3, "west", M + f"chests/blockpost_armory_{faction}")   # the armoury: the rare things
    t.set(6, 3, 5, "minecraft:spruce_fence")
    t.set(6, 4, 5, "minecraft:lantern", {"hanging": "false", "waterlogged": "false"})
    t.set(7, 3, 6, "minecraft:barrel", {"facing": "up", "open": "false"})

    # ---- covered stores (x 2..5, z 11..14): four posts, slab roof, supply chests
    for (x, z) in ((2, 11), (5, 11), (2, 14), (5, 14)):
        t.column(x, 2, 4, z, "minecraft:spruce_fence", {"north": "false", "south": "false", "east": "false",
                                                        "west": "false", "waterlogged": "false"})
    for x in range(2, 6):
        for z in range(11, 15):
            t.slab(x, 5, z, "minecraft:spruce_slab", "bottom")
    t.chest(3, 2, 14, "north", M + "chests/blockpost_supply")
    t.chest(4, 2, 14, "north", M + "chests/blockpost_supply")
    t.set(2, 2, 12, "minecraft:barrel", {"facing": "up", "open": "false"})
    t.set(5, 2, 12, "minecraft:barrel", {"facing": "up", "open": "false"})

    # ---- campfire with seats
    t.set(8, 2, 9, "minecraft:campfire", {"facing": "north", "lit": "true", "signal_fire": "false", "waterlogged": "false"})
    t.stairs(7, 2, 9, "minecraft:spruce_stairs", "east")
    t.stairs(9, 2, 9, "minecraft:spruce_stairs", "west")
    t.stairs(8, 2, 10, "minecraft:spruce_stairs", "north")

    # ---- flag pole with the flag of the squad's republic: the girder pole stands on the yard layer (y = 1) and every
    #      flag block touches the pole or the stripe next to it, so nothing floats and nothing is inside a wall
    top = H - 1
    t.pillar(POLE_X, 2, top, POLE_Z, M + "steel_girder")
    for row, stripe in enumerate(flag):
        y = top - row
        t.fill(FLAG_X0, y, POLE_Z, FLAG_X1, y, POLE_Z, stripe)

    # ---- watchtower (x 12..15, z 12..15): hollow ring, floor at y = 8, ladder inside, parapet with crenels
    t.walls(12, 2, 12, 15, 10, 15, M + "slag_bricks")
    t.air(13, 2, 13, 14, 10, 14)
    t.fill(13, 8, 13, 14, 8, 14, "minecraft:spruce_planks")
    t.set(13, 8, 13, "minecraft:air")                                    # hole for the ladder
    t.ladder(13, 2, 9, 13, "south")                                      # attached to the wall at z = 12
    t.door(12, 2, 14, "west", "minecraft:spruce_door")                   # the way in, next to the ladder
    for (x, z) in ((12, 12), (15, 12), (12, 15), (15, 15), (14, 12), (12, 14), (15, 13), (13, 15)):
        t.set(x, 10, z, "minecraft:air")                                  # crenels
    t.set(14, 9, 12, "minecraft:air")

    # ---- the garrison: sergeant at the fire, two fighters at the gate, recruits in the tower and the barracks
    t.entity(9.5, 2, 10.5, fighter_nbt(faction, 2))
    t.entity(5.5, 2, 13.5, fighter_nbt(faction, 1))
    t.entity(11.5, 2, 13.5, fighter_nbt(faction, 1))
    t.entity(14.5, 9, 14.5, fighter_nbt(faction, 0))
    t.entity(4.5, 3, 5.5, fighter_nbt(faction, 0))
    return t


def all_templates():
    return {f"military/blockpost_{f}": (build(f), G) for f in SQUADS}

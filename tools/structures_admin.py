"""The administration building of a combine ("director's office"), one 23 x 14 x 21 template.

x east, z south, y = 1 is the ground layer. A two-storey building with a portico, a reception hall and, upstairs,
the director's office (desk, shelves, a chest with the siren that calls the boss). The paved yard in front of the
portico is the arena: nothing in it, plenty of room to run.
"""
import random
import zlib

from nbt import Tpl

M = "donbass:"
SX, SY, SZ = 23, 14, 21
G = 1


def build():
    rng = random.Random(zlib.crc32(b"administration"))
    t = Tpl(SX, SY, SZ)

    # ---- yard on a foundation; the air above is cleared first
    for x in range(SX):
        for z in range(SZ):
            t.set(x, 0, z, "minecraft:coarse_dirt")
            t.set(x, 1, z, rng.choice([M + "railway_ballast", "minecraft:gravel", "minecraft:coarse_dirt",
                                       M + "spoil_gravel"]) if z > 11 else M + "slag_bricks")
    t.air(0, 2, 0, SX - 1, SY - 1, SZ - 1)

    # ---- ground floor: planks, whitewashed walls, steel corner posts
    t.fill(3, 2, 2, 19, 2, 11, "minecraft:spruce_planks")
    t.walls(3, 3, 2, 19, 6, 11, M + "whitewashed_wall")
    for (x, z) in ((3, 2), (19, 2), (3, 11), (19, 11)):
        t.pillar(x, 2, 10, z, M + "steel_girder")
    t.air(4, 3, 3, 18, 6, 10)
    for x in (5, 7, 13, 15, 17):                                           # windows, front and back
        t.set(x, 4, 2, M + "factory_glass")
        t.set(x, 4, 11, M + "factory_glass")
    for z in (4, 6, 8):                                                   # windows in the side walls
        t.set(3, 4, z, M + "factory_glass")
        t.set(19, 4, z, M + "factory_glass")
    t.door(10, 3, 11, "south", "minecraft:spruce_door", "left")           # the double door of the entrance
    t.door(11, 3, 11, "south", "minecraft:spruce_door", "right")

    # ---- second floor and the roof
    t.fill(3, 7, 2, 19, 7, 11, "minecraft:spruce_planks")
    t.walls(3, 8, 2, 19, 10, 11, M + "whitewashed_wall")
    for (x, z) in ((3, 2), (19, 2), (3, 11), (19, 11)):
        t.pillar(x, 2, 10, z, M + "steel_girder")
    t.air(4, 8, 3, 18, 10, 10)
    for x in (5, 7, 9, 11, 13, 15, 17):
        t.set(x, 9, 2, M + "factory_glass")
        t.set(x, 9, 11, M + "factory_glass")
    for z in (4, 6, 8):
        t.set(3, 9, z, M + "factory_glass")
        t.set(19, 9, z, M + "factory_glass")
    t.fill(3, 11, 2, 19, 11, 11, M + "slate_roof")
    t.fill(4, 12, 3, 18, 12, 10, M + "slate_roof")
    t.fill(6, 13, 4, 16, 13, 9, M + "slate_roof")

    # ---- ladder up to the first floor (hole in the floor at x = 4)
    t.air(4, 7, 3, 4, 7, 3)
    t.ladder(4, 3, 8, 3, "south")                                          # attached to the north wall (z = 2)

    # ---- portico: four posts, a slab roof, three steps
    for (x, z) in ((8, 13), (14, 13), (8, 12), (14, 12)):
        t.pillar(x, 2, 6, z, M + "steel_girder")
    t.fill(7, 7, 12, 15, 7, 14, M + "slate_roof")
    for x in range(9, 14):
        t.stairs(x, 2, 12, "minecraft:spruce_stairs", "south", "bottom")

    # ---- reception hall (ground floor): benches, barrels, a notice board of planks
    for x in (6, 8):
        t.stairs(x, 3, 9, "minecraft:spruce_stairs", "north")
    for x in (14, 16):
        t.stairs(x, 3, 9, "minecraft:spruce_stairs", "north")
    t.set(5, 3, 4, "minecraft:barrel", {"facing": "up", "open": "false"})
    t.set(6, 3, 4, "minecraft:barrel", {"facing": "up", "open": "false"})
    t.fill(10, 4, 3, 13, 5, 3, "minecraft:spruce_planks")                    # the board
    t.chest(18, 3, 4, "west", M + "chests/factory")                         # a plain supply chest downstairs
    t.set(11, 6, 6, "minecraft:lantern", {"hanging": "true", "waterlogged": "false"})
    t.set(16, 6, 6, "minecraft:lantern", {"hanging": "true", "waterlogged": "false"})

    # ---- the director's office (first floor, east half): carpet, desk, shelves, the chest, lamps
    t.fill(11, 8, 3, 18, 8, 10, "minecraft:red_carpet")
    t.fill(11, 8, 6, 14, 8, 6, "minecraft:dark_oak_planks")                  # the desk: a long table ...
    for x in (11, 14):
        t.set(x, 8, 7, "minecraft:dark_oak_planks")
    t.stairs(12, 8, 8, "minecraft:dark_oak_stairs", "north")                 # ... and the director's chair behind it
    t.chest(18, 8, 6, "west", M + "chests/director_office")                  # behind the desk: the siren
    for z in (3, 4, 9, 10):
        t.fill(18, 8, z, 18, 9, z, "minecraft:bookshelf")
    for x in (12, 13, 14):
        t.fill(x, 8, 10, x, 9, 10, "minecraft:bookshelf")
    t.set(14, 10, 7, "minecraft:lantern", {"hanging": "true", "waterlogged": "false"})
    t.set(7, 10, 6, "minecraft:lantern", {"hanging": "true", "waterlogged": "false"})
    t.set(7, 8, 3, "minecraft:barrel", {"facing": "up", "open": "false"})

    # ---- the arena in front: corner posts, a flag pole with a plain white pennant
    for (x, z) in ((1, 13), (21, 13), (1, 19), (21, 19)):
        t.column(x, 2, 3, z, M + "slag_block")
    t.pillar(11, 2, 10, 17, M + "steel_girder")
    t.fill(12, 9, 17, 14, 10, 17, "minecraft:white_wool")
    return t


def all_templates():
    return {"industry/administration": (build(), G)}

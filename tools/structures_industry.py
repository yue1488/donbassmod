"""Industrial complexes (steelworks, coke plant) and railway pieces (freight station,
track segments, buffer ends).  Ground layer is y = 1 for all of them (start_height -1)."""
import random
import zlib

from nbt import Tpl

M = "donbass:"
G = 1
RAIL_POOL = M + "rail/line"
TRACK = M + "track"
RAIL_STATE = "minecraft:rail[shape=east_west]"
CAMPFIRE = {"facing": "north", "lit": "true", "signal_fire": "false", "waterlogged": "false"}


def seeded(name):
    return random.Random(zlib.crc32(name.encode()))


def cyl(t, cx, cz, r, y0, y1, name, props=None):
    for y in range(y0, y1 + 1):
        t.disc(cx, cz, r, y, name, props)


def yard(t, sx, sz, rng, clear=7):
    for x in range(sx):
        for z in range(sz):
            t.set(x, 0, z, "minecraft:dirt")
            t.set(x, 1, z, rng.choice(["minecraft:gravel", M + "railway_ballast", "minecraft:coarse_dirt",
                                       M + "mine_concrete", M + "spoil_gravel", M + "railway_ballast"]))
    t.air(0, 2, 0, sx - 1, clear, sz - 1)


def perimeter_fence(t, sx, sz, gaps):
    """Fence along the border at y=2; gaps is a set of (x, z) cells left open."""
    for x in range(sx):
        for z in (0, sz - 1):
            if (x, z) not in gaps:
                t.set(x, 2, z, M + "rusty_fence")
    for z in range(sz):
        for x in (0, sx - 1):
            if (x, z) not in gaps:
                t.set(x, 2, z, M + "rusty_fence")


def stack(t, cx, cz, height, r=2):
    """Banded brick chimney with a smoking campfire at the top."""
    for y in range(2, height + 1):
        band = (y // 4) % 2 == 0
        t.ring(cx, cz, r, y, y, M + ("chimney_bricks" if band else "sooty_bricks"))
    t.set(cx, height, cz, "minecraft:campfire", CAMPFIRE)
    t.ring(cx, cz, r, height, height, M + "steel_girder", {"axis": "y"})


def wagon(t, x0, z0, length, loaded, rng, y=2):
    """A freight wagon: plated box with a coal load on top."""
    t.fill(x0, y, z0, x0 + length - 1, y + 1, z0 + 2, M + "freight_wagon_plating")
    t.fill(x0 + 1, y + 1, z0 + 1, x0 + length - 2, y + 1, z0 + 1, "minecraft:air")
    if loaded:
        t.fill(x0 + 1, y + 1, z0 + 1, x0 + length - 2, y + 1, z0 + 1, "minecraft:coal_block")
    for x in (x0, x0 + length - 1):
        t.set(x, y - 0, z0 + 1, M + "steel_girder", {"axis": "x"})


def pile(t, cx, cz, r, block, rng):
    for dy in range(r):
        rr = r - dy
        for x in range(cx - rr, cx + rr + 1):
            for z in range(cz - rr, cz + rr + 1):
                if (x - cx) ** 2 + (z - cz) ** 2 <= rr * rr:
                    t.set(x, 2 + dy, z, block if rng.random() < 0.8 else "minecraft:coal_block")


# --------------------------------------------------------------- steelworks --
def steelworks():
    SX, SZ, SH = 41, 33, 37
    t, rng = Tpl(SX, SH, SZ), seeded("steelworks")
    yard(t, SX, SZ, rng)

    # main shop hall x 2..26, z 3..14
    t.walls(2, 2, 3, 26, 3, 14, M + "slag_bricks")
    t.walls(2, 4, 3, 26, 9, 14, M + "rusty_plate")
    t.air(3, 2, 4, 25, 9, 13)
    for x in range(4, 26, 3):
        for z in (3, 14):
            t.fill(x, 7, z, x + 1, 8, z, M + "factory_glass")
    for i in range(6):                                              # stepped gable roof
        t.fill(1 + i, 10 + i, 2 + i, 27 - i, 10 + i, 15 - i, M + "slate_roof")
    t.fill(3, 1, 4, 25, 1, 13, M + "mine_concrete")
    for x in range(3, 26):
        t.set(x, 1, 8, M + "hazard_stripes")
    t.air(2, 2, 7, 2, 5, 9)                                          # rail gate in the west wall
    for x in range(0, 27):
        t.rail(x, 2, 8, "east_west")
    # overhead travelling crane
    for z in (5, 12):
        for x in range(3, 26):
            t.set(x, 8, z, M + "steel_girder", {"axis": "x"})
    for z in range(5, 13):
        t.set(14, 8, z, M + "steel_girder", {"axis": "z"})
    for y in range(4, 8):
        t.set(14, y, 8, "minecraft:chain", {"axis": "y", "waterlogged": "false"})
    t.set(14, 3, 8, "minecraft:iron_block")
    for x in range(5, 25, 4):
        t.set(x, 9, 8, M + "mine_lamp")
    # furnaces and workbenches inside
    for x in (5, 8, 11, 17, 20, 23):
        t.set(x, 2, 5, "minecraft:blast_furnace", {"facing": "south", "lit": "false"})
    t.set(22, 2, 12, "minecraft:anvil", {"facing": "east"})
    t.chest(4, 2, 12, "east", M + "chests/factory")
    t.chest(24, 2, 5, "west", M + "chests/factory")

    # blast furnace: stepped tower with girder platforms
    cx, cz = 34, 6
    cyl(t, cx, cz, 4, 2, 9, M + "slag_bricks")
    cyl(t, cx, cz, 3, 10, 20, M + "slag_bricks")
    cyl(t, cx, cz, 2, 21, 27, M + "slag_bricks")
    # work platforms: ring radius = tower radius at that height + 1, so they touch the shell
    for y, tower_r in ((10, 3), (16, 3), (22, 2)):
        t.ring(cx, cz, tower_r + 1, y, y, M + "steel_girder", {"axis": "x"})
    for y in range(2, 28, 6):
        t.ring(cx, cz, 4 if y < 10 else 3 if y < 21 else 2, y, y, M + "rusty_iron_block")
    cyl(t, cx, cz, 2, 3, 9, "minecraft:air")                         # hot-metal chamber
    t.disc(cx, cz, 2, 2, "minecraft:magma_block")
    t.air(cx, 21, cz, cx, 26, cz)
    t.set(cx, 28, cz, "minecraft:campfire", CAMPFIRE)
    t.air(cx, 3, cz + 2, cx, 4, cz + 3)                              # passage through the 2-thick shell
    t.door(cx, 3, cz + 4, "south", "minecraft:iron_door")
    # hot-blast stoves with a pipe back to the furnace
    for sx in (31, 36):
        cyl(t, sx, 16, 2, 2, 18, M + "chimney_bricks")
        t.disc(sx, 16, 2, 19, M + "slate_roof")
    for z in range(10, 14):
        t.set(34, 9, z, M + "steel_girder", {"axis": "z"})
    for x in range(31, 37):
        t.set(x, 9, 13, M + "steel_girder", {"axis": "x"})

    # smokestacks
    stack(t, 30, 26, 31)
    stack(t, 36, 27, 27)

    # coal bunker with piles
    t.walls(2, 2, 19, 10, 4, 24, M + "mine_concrete")
    t.air(3, 2, 20, 9, 4, 23)
    t.air(5, 2, 19, 7, 3, 19)
    pile(t, 6, 22, 2, M + "anthracite_block", rng)

    # office, two floors
    t.walls(14, 2, 21, 24, 4, 29, M + "sooty_bricks")
    t.fill(14, 1, 21, 24, 1, 29, "minecraft:spruce_planks")
    t.air(15, 2, 22, 23, 4, 28)
    t.fill(14, 5, 21, 24, 5, 29, M + "slate_roof")
    for x in range(16, 24, 2):
        t.set(x, 3, 21, M + "factory_glass")
    t.door(19, 2, 21, "north", "minecraft:spruce_door")
    t.chest(23, 2, 28, "north", M + "chests/factory")
    t.set(15, 2, 27, "minecraft:crafting_table")
    t.set(19, 4, 25, M + "mine_lamp")

    # slag heap in the corner
    for dy, r in enumerate((3, 2, 1)):                               # z 25..31, clear of the bunker wall at z=24
        t.disc(5, 28, r, 2 + dy, M + ("burnt_spoil" if dy % 2 == 0 else "spoil_rock"))
    t.set(5, 5, 28, M + "smoldering_spoil")

    # siding with loaded wagons
    for x in range(0, 28):
        t.rail(x, 2, 17, "east_west")
    for x0 in (3, 11, 19):
        wagon(t, x0, 16, 6, True, rng)

    perimeter_fence(t, SX, SZ, {(0, 8), (0, 17)} | {(x, SZ - 1) for x in range(18, 23)})
    return t


# --------------------------------------------------------------- coke plant --
def coke_plant():
    SX, SZ, SH = 37, 27, 31
    t, rng = Tpl(SX, SH, SZ), seeded("coke_plant")
    yard(t, SX, SZ, rng)

    # coke oven battery with iron oven doors on the front face
    t.fill(3, 2, 8, 27, 9, 14, M + "sooty_bricks")
    for x in range(4, 27, 3):
        t.fill(x, 3, 8, x, 6, 8, M + "rusty_iron_block")
        t.set(x, 7, 8, "minecraft:iron_bars")
    for x in range(3, 28, 3):
        t.column(x, 2, 9, 8, M + "chimney_bricks")
    t.fill(3, 10, 8, 27, 10, 14, M + "steel_girder", {"axis": "x"})
    for x in range(5, 27, 4):
        t.set(x, 10, 11, "minecraft:magma_block")                    # glowing charging holes
    for x in range(3, 28):
        t.rail(x, 11, 11, "east_west")
        t.set(x, 11, 10, M + "rusty_fence")
        t.set(x, 11, 12, M + "rusty_fence")
    wagon(t, 9, 10, 5, True, rng, y=12)                              # charging car on top
    t.fill(3, 2, 15, 27, 2, 15, M + "hazard_stripes")

    # quench tower
    t.walls(31, 2, 9, 35, 4, 13, M + "slag_bricks")
    for y in range(5, 19):
        t.walls(31, y, 9, 35, y, 13, M + ("rusty_fence" if y % 4 else "steel_girder"),
                {"axis": "x"} if y % 4 == 0 else None)
    t.fill(31, 19, 9, 35, 19, 13, M + "slate_roof")
    t.set(33, 20, 11, "minecraft:campfire", CAMPFIRE)
    t.air(32, 2, 10, 34, 18, 12)
    t.door(33, 2, 13, "south", "minecraft:iron_door")

    # coal / coke / anthracite heaps and a gantry to the battery
    pile(t, 7, 19, 3, M + "coke_block", rng)                         # z 16..22, clear of the siding at z=23..25
    pile(t, 16, 19, 3, "minecraft:coal_block", rng)
    pile(t, 25, 19, 3, M + "anthracite_block", rng)
    for z in range(11, 19):
        t.set(8, 12, z, M + "steel_girder", {"axis": "z"})
    for z in (16, 18):
        t.pillar(8, 2, 11, z, M + "steel_girder")

    stack(t, 3, 4, 26)
    # office
    t.walls(17, 2, 2, 25, 4, 6, M + "sooty_bricks")
    t.fill(17, 1, 2, 25, 1, 6, "minecraft:spruce_planks")
    t.air(18, 2, 3, 24, 4, 5)
    t.fill(17, 5, 2, 25, 5, 6, M + "slate_roof")
    t.door(21, 2, 6, "south", "minecraft:spruce_door")
    t.set(19, 3, 6, M + "factory_glass")
    t.set(23, 3, 6, M + "factory_glass")
    t.chest(24, 2, 3, "south", M + "chests/factory")
    t.set(21, 4, 4, M + "mine_lamp")

    # siding with coke wagons
    for x in range(0, SX):
        t.rail(x, 2, 24, "east_west")
    for x0 in (4, 12, 20):
        wagon(t, x0, 23, 6, True, rng)                               # z 23..25, fence runs at z=26
    perimeter_fence(t, SX, SZ, {(0, 24), (SX - 1, 24)} | {(x, 0) for x in range(10, 14)})
    return t


# ---------------------------------------------------------- freight station --
def freight_station():
    SX, SZ, SH = 25, 21, 12
    t, rng = Tpl(SX, SH, SZ), seeded("freight_station")
    for x in range(SX):
        for z in range(SZ):
            t.set(x, 0, z, "minecraft:dirt")
            t.set(x, 1, z, M + "railway_ballast" if 2 <= z <= 12 else rng.choice(
                ["minecraft:coarse_dirt", "minecraft:gravel", M + "railway_ballast"]))
    t.air(0, 2, 0, SX - 1, 9, SZ - 1)
    for tz in (4, 7, 10):                                            # three tracks with sleepers
        for x in range(SX):
            if x % 2 == 0:
                for z in (tz - 1, tz, tz + 1):
                    t.set(x, 1, z, M + "rail_sleepers", {"axis": "z"})
            t.rail(x, 2, tz, "east_west")
    # platform with a canopy
    t.fill(2, 1, 13, 22, 1, 15, M + "mine_concrete")
    t.fill(2, 2, 13, 22, 2, 13, M + "mine_concrete_slab", {"type": "bottom", "waterlogged": "false"})
    for x in (4, 10, 16, 22):
        t.pillar(x, 2, 6, 14, M + "steel_girder")
    t.fill(2, 7, 12, 23, 7, 15, M + "slate_roof")
    for x in (7, 13, 19):
        t.set(x, 6, 14, M + "mine_lamp")
    # station building
    t.walls(4, 2, 16, 14, 4, 20, M + "sooty_bricks")
    t.fill(4, 1, 16, 14, 1, 20, "minecraft:spruce_planks")
    t.air(5, 2, 17, 13, 4, 19)
    t.fill(3, 5, 16, 15, 5, 20, M + "slate_roof")
    t.fill(4, 6, 17, 14, 6, 19, M + "slate_roof")
    t.door(9, 2, 16, "north", "minecraft:spruce_door")
    for x in (6, 12):
        t.set(x, 3, 16, M + "factory_glass")
    t.chest(6, 2, 19, "north", M + "chests/freight_station")
    t.chest(12, 2, 19, "north", M + "chests/freight_station")
    t.set(9, 4, 18, M + "mine_lamp")
    # goods shed
    t.walls(17, 2, 16, 23, 4, 20, M + "slag_bricks")
    t.air(18, 2, 17, 22, 4, 19)
    t.air(18, 2, 16, 22, 3, 16)                                      # open to the platform
    t.fill(17, 5, 16, 23, 5, 20, M + "mine_timber_planks")
    for x in (19, 21):
        t.set(x, 2, 19, "minecraft:barrel", {"facing": "up", "open": "false"})
    t.chest(22, 2, 19, "north", M + "chests/freight_station")
    # water crane for steam locomotives
    t.pillar(1, 2, 6, 13, M + "steel_girder")
    t.set(1, 7, 13, "minecraft:cauldron")
    # diesel shunter on the middle track
    t.fill(7, 2, 6, 14, 4, 8, M + "rusty_plate")
    t.fill(7, 2, 6, 8, 4, 8, M + "hazard_stripes")
    t.air(9, 3, 7, 12, 4, 7)
    for x in (9, 12):
        t.set(x, 4, 6, M + "factory_glass")
        t.set(x, 4, 8, M + "factory_glass")
    t.column(13, 5, 7, 7, M + "chimney_bricks")
    for x in (0, 1, 2, 3, 15, 16):
        t.rail(x, 2, 7, "east_west")
    wagon(t, 4, 3, 7, True, rng)
    wagon(t, 13, 3, 7, False, rng)
    for x in range(21, 25):
        t.rail(x, 2, 10, "east_west")
    # buffer stops at the dead-end track
    t.set(24, 2, 10, M + "hazard_stripes")
    t.set(24, 3, 10, M + "steel_girder", {"axis": "y"})
    # jigsaw connectors continue the main track (middle track z=7)
    t.jigsaw(0, 2, 7, "west_up", RAIL_POOL, TRACK, TRACK, RAIL_STATE)
    t.jigsaw(SX - 1, 2, 7, "east_up", RAIL_POOL, TRACK, TRACK, RAIL_STATE)
    return t


# ------------------------------------------------------------ track pieces --
def line_base(name, length=16):
    t, rng = Tpl(length, 9, 5), seeded(name)
    for x in range(length):
        for z in range(5):
            t.set(x, 0, z, M + "railway_ballast")
        for z in (1, 2, 3):
            if x % 2 == 0:
                t.set(x, 1, z, M + "rail_sleepers", {"axis": "z"})
            else:
                t.set(x, 1, z, M + "railway_ballast")
        t.set(x, 2, 2, "minecraft:rail", {"shape": "east_west", "waterlogged": "false"})
    t.air(0, 3, 0, length - 1, 8, 4)
    return t, rng


def line_connectors(t, length):
    t.jigsaw(0, 2, 2, "west_up", RAIL_POOL, TRACK, TRACK, RAIL_STATE)
    t.jigsaw(length - 1, 2, 2, "east_up", RAIL_POOL, TRACK, TRACK, RAIL_STATE)


def line_plain():
    t, rng = line_base("line_plain")
    line_connectors(t, 16)
    return t


def line_signal():
    t, rng = line_base("line_signal")
    t.pillar(8, 2, 6, 0, M + "steel_girder")
    t.set(8, 7, 0, M + "mine_lamp")
    t.set(8, 3, 1, M + "hazard_stripes")
    line_connectors(t, 16)
    return t


def line_wreck():
    """A derelict wagon rusting on a siding next to the line."""
    t, rng = line_base("line_wreck")
    t.fill(3, 2, 0, 10, 4, 0, M + "rusty_plate")
    t.fill(3, 2, 1, 3, 4, 1, M + "rusty_plate")
    t.fill(10, 2, 1, 10, 4, 1, M + "rusty_plate")
    t.air(5, 4, 0, 8, 4, 0)
    t.set(6, 2, 1, "minecraft:cobweb")
    t.chest(7, 2, 1, "south", M + "chests/freight_station")
    line_connectors(t, 16)
    return t


def line_crossing():
    """Level crossing: a gravel road crossing the line with warning stripes."""
    t, rng = line_base("line_crossing")
    for z in range(5):
        for x in (7, 8):
            t.set(x, 1, z, "minecraft:gravel")
    t.set(7, 2, 2, "minecraft:rail", {"shape": "east_west", "waterlogged": "false"})
    t.set(8, 2, 2, "minecraft:rail", {"shape": "east_west", "waterlogged": "false"})
    for x in (5, 10):
        t.set(x, 2, 0, M + "hazard_stripes")
        t.set(x, 2, 4, M + "hazard_stripes")
    line_connectors(t, 16)
    return t


def line_end():
    """End of the branch line: buffer stop and a rusty warning post."""
    t, rng = line_base("line_end", 8)
    for x in range(5, 8):
        t.air(x, 2, 2, x, 2, 2)
    t.set(5, 2, 2, M + "hazard_stripes")
    t.set(5, 3, 2, M + "steel_girder", {"axis": "y"})
    t.set(5, 4, 2, M + "mine_lamp")
    t.set(6, 2, 1, M + "rusty_iron_block")
    t.set(6, 2, 3, M + "rusty_iron_block")
    t.jigsaw(0, 2, 2, "west_up", RAIL_POOL, TRACK, TRACK, RAIL_STATE)
    return t


def all_templates():
    return {
        "industry/steelworks": (steelworks(), G),
        "industry/coke_plant": (coke_plant(), G),
        "rail/freight_station": (freight_station(), G),
        "rail/line_plain": (line_plain(), G),
        "rail/line_signal": (line_signal(), G),
        "rail/line_wreck": (line_wreck(), G),
        "rail/line_crossing": (line_crossing(), G),
        "rail/line_end": (line_end(), G),
    }

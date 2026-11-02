"""Worker settlement: plaza centres and street plots (jigsaw pieces), 13 x 13 each.

Plot layout (x east, z south): the street runs along z = 5..7 and is connected at both
ends (x = 0 and x = 12) by jigsaw blocks; a building plot of 5 rows lies north (z 0..4) and
a mirrored one south (z 8..12).  Ground layer is y = 1 (y = 0 is foundation), so the
structure start_height is -1.
"""
import random
import zlib

from nbt import Tpl

M = "donbass:"
S = 13
H = 17
G = 1
POOL_PLOTS = M + "settlement/plots"
STREET = M + "street"
PATH = "minecraft:dirt_path"
GRASS = ("minecraft:grass_block", {"snowy": "false"})


def seeded(name):
    return random.Random(zlib.crc32(name.encode()))


def new():
    return Tpl(S, H, S)


# ---------------------------------------------------------------- houses ----
def roof(t, y, x0, x1, z0, z1, block):
    """Two-step roof: wide eave layer at y, narrower ridge layer at y+1."""
    t.fill(x0, y, z0, x1, y, z1, block)
    t.fill(x0 + 1, y + 1, z0 + 1, x1 - 1, y + 1, z1 - 1, block)


def house_door(t, x=6, z=4):
    t.door(x, 2, z, "south", "minecraft:spruce_door")


def furnish(t, bed_xz, chest_xz, rng):
    t.bed(bed_xz[0], 2, bed_xz[1], "south", rng.choice(["red", "blue", "gray"]))
    t.chest(chest_xz[0], 2, chest_xz[1], "south", M + "chests/settlement_house")
    t.set(6, 4, 2, M + "mine_lamp")


def brick_house(name):
    t, rng = new(), seeded(name)
    t.fill(3, 0, 0, 9, 0, 4, "minecraft:cobblestone")
    t.fill(3, 1, 0, 9, 1, 4, "minecraft:spruce_planks")
    t.walls(3, 2, 0, 9, 4, 4, M + "sooty_bricks")
    t.air(4, 2, 1, 8, 4, 3)
    roof(t, 5, 2, 10, 0, 4, M + "slate_roof")
    for x in (4, 8):
        t.set(x, 3, 4, M + "factory_glass")
    t.set(3, 3, 2, M + "factory_glass")
    t.set(9, 3, 2, M + "factory_glass")
    house_door(t)
    furnish(t, (4, 1), (8, 1), rng)
    for y in range(5, 9):
        t.set(8, y, 1, M + "chimney_bricks")
    return t


def hut(name):
    t, rng = new(), seeded(name)
    t.fill(3, 0, 0, 9, 0, 4, "minecraft:dirt")
    t.fill(3, 1, 0, 9, 1, 4, "minecraft:coarse_dirt")
    t.walls(3, 2, 0, 9, 4, 4, M + "whitewashed_wall")
    for (x, z) in ((3, 0), (9, 0), (3, 4), (9, 4)):
        t.pillar(x, 2, 4, z, M + "mine_timber_beam")
    t.air(4, 2, 1, 8, 4, 3)
    t.fill(2, 5, 0, 10, 5, 4, "minecraft:hay_block", {"axis": "y"})
    t.fill(3, 6, 1, 9, 6, 3, "minecraft:hay_block", {"axis": "y"})
    t.set(5, 3, 4, M + "factory_glass")
    t.set(7, 3, 4, M + "factory_glass")
    house_door(t)
    furnish(t, (4, 1), (8, 1), rng)
    # low wattle fence and a sunflower
    for x in (1, 2, 10, 11):
        t.set(x, 2, 3, "minecraft:oak_fence", {"north": "false", "south": "false", "east": "false",
                                                "west": "false", "waterlogged": "false"})
    return t


def barrack(name):
    t, rng = new(), seeded(name)
    t.fill(1, 0, 1, 11, 0, 4, "minecraft:cobblestone")
    t.fill(1, 1, 1, 11, 1, 4, "minecraft:spruce_planks")
    t.walls(1, 2, 1, 11, 4, 4, M + "whitewashed_wall")
    t.air(2, 2, 2, 10, 4, 3)
    roof(t, 5, 0, 12, 1, 4, M + "slate_roof")
    for x in (3, 6, 9):
        t.door(x, 2, 4, "south", "minecraft:spruce_door")
    for x in (2, 4, 5, 7, 8, 10):
        t.set(x, 3, 4, M + "factory_glass")
    for x, c in ((2, "red"), (5, "gray"), (8, "blue")):
        t.bed(x, 2, 2, "south", c)
    t.chest(10, 2, 2, "south", M + "chests/settlement_house")
    for x in (4, 7):
        t.set(x, 4, 2, M + "mine_lamp")
    return t


def panel_block(name):
    """Three-storey prefab apartment block (khrushchyovka)."""
    t, rng = new(), seeded(name)
    t.fill(1, 0, 0, 11, 0, 4, M + "mine_concrete")
    t.fill(1, 1, 0, 11, 1, 4, M + "mine_concrete")
    for floor in range(3):
        y0 = 2 + floor * 4
        t.walls(1, y0, 0, 11, y0 + 2, 4, M + "prefab_panel")
        t.air(2, y0, 1, 10, y0 + 2, 3)
        t.fill(1, y0 + 3, 0, 11, y0 + 3, 4, M + "mine_concrete")      # floor slab / roof
        for x in range(2, 11, 2):
            t.set(x, y0 + 1, 4, M + "factory_glass")
        t.set(5, y0 + 2, 2, M + "mine_lamp")
        t.set(8, y0 + 2, 2, M + "mine_lamp")
    t.door(6, 2, 4, "south", "minecraft:iron_door")
    # stair shaft: ladder up the north wall with holes in the slabs
    t.ladder(10, 2, 12, 1, "south")
    for y in (5, 9):
        t.set(10, y, 1, "minecraft:air")
    t.ladder(10, 5, 5, 1, "south")
    t.ladder(10, 9, 9, 1, "south")
    t.fill(1, 14, 0, 11, 14, 4, M + "slate_roof")
    t.chest(3, 10, 1, "south", M + "chests/settlement_house")
    t.chest(3, 2, 1, "south", M + "chests/settlement_house")
    return t


def shop(name):
    t, rng = new(), seeded(name)
    t.fill(3, 0, 0, 9, 0, 4, "minecraft:cobblestone")
    t.fill(3, 1, 0, 9, 1, 4, M + "polished_slag")
    t.walls(3, 2, 0, 9, 4, 4, "minecraft:bricks")
    t.air(4, 2, 1, 8, 4, 3)
    roof(t, 5, 2, 10, 0, 4, M + "slate_roof")
    for x in (4, 5, 7, 8):
        t.set(x, 3, 4, M + "factory_glass")
        t.set(x, 2, 4, M + "factory_glass")
    for x in range(3, 10):
        t.set(x, 4, 4, M + "freight_wagon_plating")                   # awning band
    house_door(t)
    t.set(4, 2, 1, "minecraft:barrel", {"facing": "up", "open": "false"})
    t.set(5, 2, 1, "minecraft:barrel", {"facing": "up", "open": "false"})
    t.chest(8, 2, 1, "south", M + "chests/settlement_house")
    t.set(6, 4, 2, M + "mine_lamp")
    return t


def garden(name):
    t, rng = new(), seeded(name)
    t.fill(1, 0, 0, 11, 0, 4, "minecraft:dirt")
    for x in range(2, 11):
        for z in range(0, 4):
            if (x, z) == (6, 1):
                t.set(x, 1, z, "minecraft:water", {"level": "0"})
                continue
            t.set(x, 1, z, "minecraft:farmland", {"moisture": "7"})
            # age 0..3 is valid for carrots, potatoes (0..7) and beetroots (0..3)
            t.set(x, 2, z, rng.choice(["minecraft:carrots", "minecraft:potatoes", "minecraft:beetroots"]),
                  {"age": str(rng.randint(0, 3))})
    t.set(6, 2, 1, "minecraft:air")
    for x in range(1, 12):
        t.set(x, 2, 4, "minecraft:oak_fence", {"north": "false", "south": "false", "east": "false",
                                                "west": "false", "waterlogged": "false"})
    t.set(6, 2, 4, "minecraft:air")                                    # gate gap to the street
    return t


def coal_shed(name):
    t, rng = new(), seeded(name)
    t.fill(3, 0, 0, 9, 0, 4, "minecraft:dirt")
    t.fill(3, 1, 0, 9, 1, 4, M + "railway_ballast")
    t.walls(3, 2, 0, 9, 3, 4, M + "slag_block")
    t.air(4, 2, 1, 8, 3, 3)
    t.air(5, 2, 4, 7, 3, 4)                                            # open front
    t.fill(2, 4, 0, 10, 4, 4, M + "mine_timber_planks")
    for x in range(4, 9):
        for z in (1, 2):
            t.set(x, 2, z, "minecraft:coal_block")
    t.set(5, 3, 1, "minecraft:coal_block")
    t.set(6, 3, 1, "minecraft:coal_block")
    t.set(7, 2, 3, M + "anthracite_block")
    t.chest(8, 2, 3, "south", M + "chests/settlement_house")
    return t


def well(name):
    t, rng = new(), seeded(name)
    t.fill(1, 0, 0, 11, 0, 4, "minecraft:dirt")
    t.fill(5, 1, 1, 7, 1, 3, "minecraft:cobblestone")
    t.set(6, 1, 2, "minecraft:water", {"level": "0"})
    for (x, z) in ((5, 1), (7, 1), (5, 3), (7, 3)):
        t.set(x, 2, z, "minecraft:cobblestone_wall", {"up": "true", "north": "none", "south": "none",
                                                      "east": "none", "west": "none", "waterlogged": "false"})
        t.pillar(x, 3, 4, z, M + "mine_timber_beam")
    t.fill(4, 5, 0, 8, 5, 4, M + "mine_timber_planks")
    t.set(6, 4, 2, "minecraft:chain", {"axis": "y", "waterlogged": "false"})
    t.set(6, 3, 2, "minecraft:lantern", {"hanging": "true", "waterlogged": "false"})
    t.set(2, 2, 3, "minecraft:cauldron")
    t.set(10, 2, 3, "minecraft:barrel", {"facing": "up", "open": "false"})
    return t


BUILDERS = {"brick": brick_house, "hut": hut, "barrack": barrack, "panel": panel_block, "shop": shop,
            "garden": garden, "shed": coal_shed, "well": well}

# (north building, south building, pool weight)
PAIRS = [("brick", "hut", 5), ("hut", "hut", 4), ("brick", "brick", 4), ("barrack", "garden", 3),
         ("panel", "brick", 2), ("shop", "hut", 2), ("garden", "shed", 2), ("well", "brick", 2),
         ("hut", "garden", 3), ("barrack", "barrack", 2), ("panel", "panel", 1), ("shed", "well", 1),
         ("brick", "shop", 2), ("hut", "brick", 3)]


def base_plot():
    t = new()
    for x in range(S):
        for z in range(S):
            t.set(x, 0, z, "minecraft:dirt")
            if 5 <= z <= 7:
                t.set(x, 1, z, PATH)
            else:
                t.set(x, 1, z, GRASS[0], GRASS[1])
    t.air(0, 2, 0, S - 1, 6, S - 1)
    return t


def street_lamp(t, x, z):
    t.pillar(x, 2, 4, z, M + "steel_girder")
    t.set(x, 5, z, M + "mine_lamp")


def build_plot(i, north, south):
    name = f"plot_{i}_{north}_{south}"
    t = base_plot()
    t.paste(BUILDERS[north](name + "_n"), 0, 0, 0)
    t.paste(BUILDERS[south](name + "_s").mirrored_z(), 0, 0, 0)
    street_lamp(t, 2, 5)
    street_lamp(t, 10, 7)
    # the street ends are jigsaw connectors (replaced by path blocks after generation)
    t.jigsaw(0, 1, 6, "west_up", POOL_PLOTS, STREET, STREET, PATH)
    t.jigsaw(12, 1, 6, "east_up", POOL_PLOTS, STREET, STREET, PATH)
    return name, t


# ----------------------------------------------------------- plaza centres --
def plaza_base(name):
    t, rng = new(), seeded(name)
    for x in range(S):
        for z in range(S):
            t.set(x, 0, z, "minecraft:dirt")
            on_road = 5 <= z <= 7 or 5 <= x <= 7
            if on_road:
                t.set(x, 1, z, M + ("polished_slag" if (x + z) % 2 else "slag_bricks"))
            else:
                t.set(x, 1, z, *GRASS)
    t.air(0, 2, 0, S - 1, 12, S - 1)
    for (x, z) in ((3, 3), (9, 3), (3, 9), (9, 9)):
        street_lamp(t, x, z)
    return t, rng


def connectors(t):
    t.jigsaw(0, 1, 6, "west_up", POOL_PLOTS, STREET, STREET, PATH)
    t.jigsaw(12, 1, 6, "east_up", POOL_PLOTS, STREET, STREET, PATH)
    t.jigsaw(6, 1, 0, "north_up", POOL_PLOTS, STREET, STREET, PATH)
    t.jigsaw(6, 1, 12, "south_up", POOL_PLOTS, STREET, STREET, PATH)


def center_monument():
    """Monument to the miner: a pit-wheel on a plinth, ringed by coal-bunker benches."""
    t, rng = plaza_base("center_monument")
    t.fill(5, 2, 5, 7, 2, 7, M + "slag_bricks")
    t.fill(6, 3, 6, 6, 3, 6, M + "slag_bricks")
    t.column(6, 4, 7, 6, M + "mine_concrete")
    t.wheel(6, 9, 6, 3, "minecraft:iron_bars")
    t.set(6, 9, 6, "minecraft:iron_block")
    t.set(6, 12, 6, M + "mine_lamp")
    for (x, z) in ((5, 5), (7, 5), (5, 7), (7, 7)):
        t.set(x, 3, z, M + "coal_bunker")
    t.chest(4, 2, 6, "east", M + "chests/settlement_house")
    connectors(t)
    return t


def center_water_tower():
    """Brick water tower with a riveted iron tank."""
    t, rng = plaza_base("center_water_tower")
    for (x, z) in ((5, 5), (7, 5), (5, 7), (7, 7)):
        t.column(x, 2, 8, z, M + "chimney_bricks")
    for y in (4, 7):
        for x in range(5, 8):
            for z in range(5, 8):
                if x in (5, 7) or z in (5, 7):
                    t.set(x, y, z, M + "sooty_bricks")
    t.fill(4, 9, 4, 8, 9, 8, M + "rusty_plate")
    for y in (10, 11, 12):
        t.walls(4, y, 4, 8, y, 8, M + "rusty_iron_block")
        if y < 12:
            t.fill(5, y, 5, 7, y, 7, "minecraft:water", {"level": "0"})
    t.fill(4, 13, 4, 8, 13, 8, M + "slate_roof")
    # ladder between the two south legs; it is attached to the west leg at (5, y, 7)
    t.ladder(6, 2, 8, 7, "east")
    t.set(6, 14, 6, M + "mine_lamp")
    connectors(t)
    return t


def all_templates():
    out = {"settlement/center_monument": (center_monument(), G),
           "settlement/center_water_tower": (center_water_tower(), G)}
    weights = {}
    for i, (n, s, w) in enumerate(PAIRS):
        name, t = build_plot(i, n, s)
        out["settlement/" + name] = (t, G)
        weights["settlement/" + name] = w
    return out, weights

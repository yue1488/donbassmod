"""Generates all data-driven world generation JSON for the Donbass mod:
dimension, noise settings, biomes, carvers, features, processors, template pools,
structures, structure sets, tags and chest loot tables.

Formats were checked against vanilla 1.20.1 data (misode/mcmeta tag 1.20.1-data-json);
the vanilla files used as bases are kept in tools/reference/.
"""
import copy
import json
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.normpath(os.path.join(HERE, ".."))
DATA = os.path.join(PROJ, "src", "main", "resources", "data", "donbass")
WG = os.path.join(DATA, "worldgen")
REF = os.path.join(HERE, "reference")
N = "donbass:"


def wj(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


def ref(name):
    with open(os.path.join(REF, name), encoding="utf-8") as f:
        return json.load(f)


# ------------------------------------------------------------ terrain -------
def gen_terrain():
    # Gentle rolling steppe: a vertical gradient (surface where it crosses 0, ~y=78)
    # plus two 2D noises (broad swells + small bumps).  y_scale 0 => no overhangs.
    base = {
        "type": "minecraft:add",
        "argument1": {"type": "minecraft:y_clamped_gradient", "from_y": -64, "to_y": 220,
                      "from_value": 1.5, "to_value": -1.5},
        "argument2": {
            "type": "minecraft:add",
            "argument1": {"type": "minecraft:mul", "argument1": 0.16,
                          "argument2": {"type": "minecraft:noise", "noise": "minecraft:erosion",
                                        "xz_scale": 2.0, "y_scale": 0.0}},
            "argument2": {"type": "minecraft:mul", "argument1": 0.05,
                          "argument2": {"type": "minecraft:noise", "noise": "minecraft:surface",
                                        "xz_scale": 0.5, "y_scale": 0.0}}}}
    wj(os.path.join(WG, "density_function", "steppe", "base.json"), base)

    shifted = lambda n: {"type": "minecraft:shifted_noise", "noise": "minecraft:" + n,
                         "shift_x": "minecraft:shift_x", "shift_y": 0.0, "shift_z": "minecraft:shift_z",
                         "xz_scale": 0.25, "y_scale": 0.0}
    rule_block = lambda name, props=None: {"type": "minecraft:block", "result_state":
                                           dict({"Name": name}, **({"Properties": props} if props else {}))}
    cond = lambda c, then: {"type": "minecraft:condition", "if_true": c, "then_run": then}
    stone_floor = lambda depth: {"type": "minecraft:stone_depth", "offset": 0, "surface_type": "floor",
                                 "add_surface_depth": depth, "secondary_depth_range": 0}
    surface = {"type": "minecraft:sequence", "sequence": [
        cond({"type": "minecraft:vertical_gradient", "random_name": "minecraft:bedrock_floor",
              "true_at_and_below": {"above_bottom": 0}, "false_at_and_above": {"above_bottom": 5}},
             rule_block("minecraft:bedrock")),
        cond({"type": "minecraft:above_preliminary_surface"}, {"type": "minecraft:sequence", "sequence": [
            cond(stone_floor(False), {"type": "minecraft:sequence", "sequence": [
                cond({"type": "minecraft:water", "offset": -1, "surface_depth_multiplier": 0,
                      "add_stone_depth": False},
                     rule_block("minecraft:grass_block", {"snowy": "false"})),
                rule_block("minecraft:dirt")]}),
            cond(stone_floor(True), rule_block("minecraft:dirt"))]}),
        cond({"type": "minecraft:vertical_gradient", "random_name": "minecraft:deepslate",
              "true_at_and_below": {"absolute": 0}, "false_at_and_above": {"absolute": 8}},
             rule_block("minecraft:deepslate", {"axis": "y"}))]}

    wj(os.path.join(WG, "noise_settings", "steppe.json"), {
        "sea_level": 63, "disable_mob_generation": False, "aquifers_enabled": False,
        "ore_veins_enabled": False, "legacy_random_source": False,
        "default_block": {"Name": "minecraft:stone"},
        "default_fluid": {"Name": "minecraft:water", "Properties": {"level": "0"}},
        "noise": {"min_y": -64, "height": 384, "size_horizontal": 1, "size_vertical": 2},
        "noise_router": {
            "barrier": 0.0, "fluid_level_floodedness": 0.0, "fluid_level_spread": 0.0, "lava": 0.0,
            "temperature": shifted("temperature"), "vegetation": shifted("vegetation"),
            "continents": 0.0, "erosion": 0.0, "depth": 0.0, "ridges": 0.0,
            "initial_density_without_jaggedness": N + "steppe/base",
            "final_density": {"type": "minecraft:interpolated", "argument": N + "steppe/base"},
            "vein_toggle": 0.0, "vein_ridged": 0.0, "vein_gap": 0.0},
        "spawn_target": [],
        "surface_rule": surface})

    def entry(biome, hum):
        return {"biome": N + biome, "parameters": {
            "temperature": [-1.0, 1.0], "humidity": hum, "continentalness": [-1.2, 1.0],
            "erosion": [-1.0, 1.0], "weirdness": [-1.0, 1.0], "depth": 0.0, "offset": 0.0}}

    wj(os.path.join(DATA, "dimension", "donbass.json"), {
        "type": "minecraft:overworld",
        "generator": {"type": "minecraft:noise", "settings": N + "steppe",
                      "biome_source": {"type": "minecraft:multi_noise", "biomes": [
                          entry("steppe", [-1.0, 0.3]), entry("balka", [0.3, 1.0])]}}})


# ------------------------------------------------------------- biomes -------
def gen_biomes():
    plains = ref("plains_1.20.1.json")
    feats = plains["features"]

    def make(variant):
        b = copy.deepcopy(plains)
        steps = [list(s) for s in feats]
        steps[2] = []                                  # no amethyst geodes
        steps[4] = [N + "terricone"]                   # surface structures: spoil heaps
        steps[6] = [f for f in steps[6] if f not in ("minecraft:ore_diamond_buried",)] + \
                   [N + "coal_seam_upper", N + "coal_seam_deep", N + "anthracite_ore", N + "anthracite_ore_buried"]
        if variant == "steppe":
            steps[9] = ["minecraft:patch_grass_plain", "minecraft:patch_tall_grass_2", "minecraft:trees_plains",
                        "minecraft:flower_plains", "minecraft:patch_berry_common"]
            b["temperature"], b["downfall"] = 0.75, 0.25
            b["effects"].update({"grass_color": 0xB4B25A, "foliage_color": 0x9AA050,
                                 "sky_color": 0x7FA8F0, "fog_color": 0xC8D4E6})
            b["carvers"] = {"air": ["minecraft:cave", "minecraft:cave_extra_underground"]}
        else:  # balka: wooded gully with ravines
            steps[9] = ["minecraft:patch_grass_plain", "minecraft:trees_birch", "minecraft:flower_default",
                        "minecraft:patch_berry_common"]
            b["temperature"], b["downfall"] = 0.7, 0.5
            b["effects"].update({"grass_color": 0x8DB04F, "foliage_color": 0x77A03F,
                                 "sky_color": 0x7FA8F0, "fog_color": 0xC8D4E6})
            b["carvers"] = {"air": ["minecraft:cave", "minecraft:cave_extra_underground", N + "balka_canyon"]}
        b["features"] = steps
        return b

    wj(os.path.join(WG, "biome", "steppe.json"), make("steppe"))
    wj(os.path.join(WG, "biome", "balka.json"), make("balka"))

    canyon = ref("canyon_1.20.1.json")
    canyon["config"]["probability"] = 0.09
    canyon["config"]["y"] = {"type": "minecraft:uniform", "min_inclusive": {"absolute": 40},
                             "max_inclusive": {"absolute": 70}}
    canyon["config"]["shape"]["thickness"]["value"] = {"max": 5.0, "min": 0.0, "plateau": 1.0}
    wj(os.path.join(WG, "configured_carver", "balka_canyon.json"), canyon)

    # Structures spawn ONLY in the Donbass dimension's own biomes.  (0.2.x also listed plains, sunflower plains,
    # savanna and meadow here, so the settlements, mines and checkpoints appeared in the ordinary Overworld too -
    # fixed in 0.3.1; tools/validate.py now fails if a vanilla biome gets into this tag again.)
    only_donbass = [N + "steppe", N + "balka"]
    wj(os.path.join(DATA, "tags", "worldgen", "biome", "has_structures.json"), {"values": only_donbass})
    # Coal seams and anthracite also appear in every ordinary Overworld biome (Forge biome modifier).
    wj(os.path.join(DATA, "forge", "biome_modifier", "overworld_coal.json"), {
        "type": "forge:add_features", "biomes": "#minecraft:is_overworld", "step": "underground_ores",
        "features": [N + "coal_seam_upper", N + "coal_seam_deep", N + "anthracite_ore", N + "anthracite_ore_buried"]})


# ----------------------------------------------------------- features -------
def gen_features():
    cf = lambda name, obj: wj(os.path.join(WG, "configured_feature", name + ".json"), obj)
    pf = lambda name, feat, mods: wj(os.path.join(WG, "placed_feature", name + ".json"),
                                     {"feature": N + feat, "placement": mods})
    yrange = lambda lo, hi: {"type": "minecraft:height_range", "height": {
        "type": "minecraft:uniform", "min_inclusive": {"absolute": lo}, "max_inclusive": {"absolute": hi}}}
    sq, biome = {"type": "minecraft:in_square"}, {"type": "minecraft:biome"}

    cf("coal_seam", {"type": N + "coal_seam", "config": {}})
    cf("terricone", {"type": N + "terricone", "config": {}})

    def ore(size, normal, deep):
        o = ref("ore_coal_1.20.1.json")
        o["config"]["size"] = size
        o["config"]["targets"][0]["state"]["Name"] = N + normal
        o["config"]["targets"][1]["state"]["Name"] = N + deep
        return o

    cf("anthracite_ore", ore(7, "anthracite_ore", "deepslate_anthracite_ore"))
    cf("anthracite_ore_buried", ore(5, "anthracite_ore", "deepslate_anthracite_ore"))

    pf("coal_seam_upper", "coal_seam", [{"type": "minecraft:rarity_filter", "chance": 3}, sq, yrange(30, 66), biome])
    pf("coal_seam_deep", "coal_seam", [{"type": "minecraft:rarity_filter", "chance": 4}, sq, yrange(-40, 24), biome])
    pf("anthracite_ore", "anthracite_ore", [{"type": "minecraft:count", "count": 3}, sq, yrange(-48, 20), biome])
    pf("anthracite_ore_buried", "anthracite_ore_buried",
       [{"type": "minecraft:count", "count": 2}, sq, yrange(-64, -8), biome])
    pf("terricone", "terricone", [{"type": "minecraft:rarity_filter", "chance": 20}, sq,
                                  {"type": "minecraft:heightmap", "heightmap": "WORLD_SURFACE_WG"}, biome])


# ---------------------------------------------------------- processors ------
def rule(block, prob, out):
    return {"input_predicate": {"block": block, "predicate_type": "minecraft:random_block_match", "probability": prob},
            "location_predicate": {"predicate_type": "minecraft:always_true"},
            "output_state": {"Name": out}}


def gen_processors():
    pl = lambda name, rules: wj(os.path.join(WG, "processor_list", name + ".json"),
                                {"processors": [{"processor_type": "minecraft:rule", "rules": rules}]})
    pl("weathered", [rule(N + "mine_concrete", 0.12, N + "cracked_mine_concrete"),
                     rule(N + "mine_concrete", 0.10, N + "soot_stained_concrete"),
                     rule("minecraft:bricks", 0.2, N + "sooty_bricks")])
    abandoned = [rule(N + "mine_concrete", 0.30, N + "cracked_mine_concrete"),
                 rule(N + "reinforced_mine_concrete", 0.15, N + "cracked_mine_concrete"),
                 rule(N + "mine_timber_planks", 0.20, "minecraft:air"),
                 rule(N + "mine_timber_beam", 0.08, "minecraft:air"),
                 rule(N + "mine_lamp", 0.55, "minecraft:air"),
                 rule(N + "factory_glass", 0.45, "minecraft:air"),
                 rule("minecraft:rail", 0.25, "minecraft:air"),
                 rule("minecraft:torch", 0.5, "minecraft:air"),
                 rule("minecraft:wall_torch", 0.5, "minecraft:air"),
                 rule("minecraft:lantern", 0.5, "minecraft:air"),
                 rule(N + "slag_bricks", 0.15, N + "slag_block")]
    rusted = [rule(N + "steel_girder", 0.25, N + "rusty_iron_block"),
              rule(N + "freight_wagon_plating", 0.2, N + "rusty_plate"),
              rule("minecraft:iron_bars", 0.3, N + "rusty_fence"),
              rule(N + "hazard_stripes", 0.2, N + "cracked_mine_concrete")]
    pl("abandoned", abandoned)
    pl("rusted", rusted)
    pl("ruined", abandoned + rusted)        # derelict industry: both kinds of decay


# --------------------------------------------------------------- loot -------
def gen_loot():
    """Chest and entity loot.  Design rules (0.2.0):
    * every chest has a bulk pool (resources) and, separately, at most one armour piece / tool / weapon roll, so a
      single chest can never contain a complete armour set; the military sets only come from checkpoints and fighters,
      two pieces at most per chest, and only pieces of the squad that owns the post;
    * the further down / the more guarded a structure is, the better the equipment: shallow mines give a hard hat,
      active mines miner's clothes, deep mines coal plates and coal armour, factories parts and components,
      checkpoints rifles, magazines and uniforms.
    """
    def it(name, w=1, lo=None, hi=None):
        e = {"type": "minecraft:item", "name": name if ":" in name else "minecraft:" + name, "weight": w}
        if lo is not None:
            e["functions"] = [{"function": "minecraft:set_count",
                               "count": {"type": "minecraft:uniform", "min": float(lo), "max": float(hi)},
                               "add": False}]
        return e

    def empty(w):
        return {"type": "minecraft:empty", "weight": w}

    d = lambda n: N + n
    tables = {
        # ---- mines -------------------------------------------------------------------------------------------
        "mine_shallow": [
            (2, 4, [it("coal", 14, 2, 6), it(d("coal_dust"), 10, 1, 4), it(d("iron_scrap"), 10, 1, 4),
                    it("torch", 12, 3, 8), it("stick", 8, 2, 6), it("rail", 6, 2, 8), it("bread", 6, 1, 2),
                    it(d("rusty_gear"), 4, 1, 1), it(d("miners_token"), 5, 1, 2), it("iron_nugget", 6, 2, 6),
                    it("lantern", 2, 1, 1)]),
            (1, 1, [it(d("miners_helmet"), 3), it(d("miners_boots"), 2), it(d("miners_pickaxe"), 1), empty(14)]),
        ],
        "mine_active": [
            (3, 5, [it("coal", 12, 3, 8), it(d("coke"), 8, 1, 4), it(d("anthracite"), 6, 1, 3),
                    it(d("miners_ration"), 8, 1, 3), it(d("miners_token"), 8, 1, 3), it("iron_ingot", 8, 1, 4),
                    it("torch", 10, 4, 10), it("rail", 8, 4, 12), it("powered_rail", 3, 1, 4),
                    it("iron_pickaxe", 3, 1, 1), it("minecart", 2, 1, 1), it("bread", 6, 2, 4),
                    it(d("mine_lamp"), 3, 1, 2), it("tnt", 2, 1, 2)]),
            (1, 1, [it(d("miners_helmet"), 4), it(d("miners_jacket"), 3), it(d("miners_trousers"), 3),
                    it(d("miners_boots"), 4), it(d("miners_pickaxe"), 2), empty(10)]),
            (1, 1, [it(d("rifle_cartridge"), 3, 3, 8), it(d("gun_parts"), 1), empty(14)]),
        ],
        "mine_deep": [
            (3, 6, [it(d("anthracite"), 12, 2, 6), it(d("coke"), 8, 2, 5), it("iron_ingot", 10, 2, 6),
                    it("gold_ingot", 6, 1, 3), it("redstone", 8, 3, 8), it("lapis_lazuli", 5, 2, 6),
                    it(d("coal_plate"), 5, 1, 3), it(d("miners_token"), 8, 2, 4), it(d("miners_ration"), 6, 1, 3),
                    it("tnt", 3, 1, 3), it(d("rusty_gear"), 6, 1, 2), it(d("donbass_ticket"), 2, 1, 1)]),
            (1, 1, [it(d("coal_helmet"), 2), it(d("coal_boots"), 2), it(d("coal_leggings"), 1),
                    it(d("coal_chestplate"), 1), it(d("miners_pickaxe"), 3), it("iron_pickaxe", 3),
                    it("diamond_pickaxe", 1), empty(13)]),
            (1, 1, [it(d("rifle_cartridge"), 5, 4, 10), it(d("gun_parts"), 3), it(d("rifle_magazine"), 2),
                    it(d("ak_rifle"), 1), it("diamond", 2, 1, 2), it("golden_apple", 1), empty(12)]),
        ],
        # ---- settlements ---------------------------------------------------------------------------------------
        "settlement_house": [
            (2, 4, [it("bread", 12, 1, 3), it("potato", 10, 1, 4), it("carrot", 8, 1, 3), it("beetroot", 8, 1, 3),
                    it(d("miners_ration"), 5, 1, 2), it("clay_ball", 6, 2, 6), it("coal", 8, 1, 4),
                    it("paper", 5, 1, 3), it("iron_nugget", 6, 1, 4), it(d("miners_token"), 5, 1, 2),
                    it("white_wool", 3, 1, 2), it("bone_meal", 5, 1, 3), it("leather", 4, 1, 3)]),
            (1, 1, [it(d("miners_jacket"), 3), it(d("miners_trousers"), 3), it(d("miners_boots"), 3),
                    it(d("miners_helmet"), 2), it(d("miners_pickaxe"), 1), empty(12)]),
        ],
        # ---- industry ------------------------------------------------------------------------------------------
        "factory": [
            (3, 5, [it("iron_ingot", 12, 2, 6), it(d("iron_scrap"), 10, 2, 6), it(d("rusty_gear"), 8, 1, 3),
                    it(d("coke"), 8, 2, 5), it("redstone", 6, 2, 6), it("copper_ingot", 6, 2, 5),
                    it(d("steel_girder"), 5, 1, 3), it(d("miners_token"), 5, 1, 3), it("gold_ingot", 3, 1, 2),
                    it("tnt", 2, 1, 2), it("lead", 3, 1, 2), it(d("gun_parts"), 4, 1, 2),
                    it(d("coal_plate"), 3, 1, 2), it("gunpowder", 4, 1, 3)]),
            (1, 1, [it("iron_pickaxe", 3), it(d("miners_pickaxe"), 3), it("iron_axe", 2), it("shears", 2),
                    it(d("rifle_magazine"), 2), it("diamond_pickaxe", 1), empty(12)]),
            (1, 1, [it(d("rifle_cartridge"), 3, 2, 6), empty(10)]),
        ],
        "freight_station": [
            (2, 4, [it("rail", 12, 3, 10), it("powered_rail", 5, 1, 4), it("detector_rail", 4, 1, 3),
                    it("minecart", 4, 1, 1), it("coal", 10, 2, 6), it(d("coke"), 6, 1, 3),
                    it(d("donbass_ticket"), 4, 1, 1), it(d("miners_token"), 6, 1, 3), it("paper", 6, 1, 4),
                    it("chest_minecart", 2, 1, 1), it(d("iron_scrap"), 8, 1, 4)]),
            (1, 1, [it(d("miners_boots"), 2), it(d("miners_helmet"), 2), it(d("gun_parts"), 2), empty(10)]),
        ],
        # ---- the director's office: the siren (the boss summon item) is always there, plus a few good things -----
        "director_office": [
            (1, 1, [it(d("combine_siren"), 1)]),
            (3, 5, [it(d("coal_plate"), 8, 2, 5), it(d("rifle_cartridge"), 10, 8, 24), it(d("miners_token"), 8, 4, 10),
                    it(d("gun_parts"), 3, 1, 2), it(d("rifle_magazine"), 3), it("gold_ingot", 6, 2, 5),
                    it("iron_ingot", 6, 3, 8), it("diamond", 2, 1, 1), it("book", 4, 1, 3), it("paper", 5, 2, 6),
                    it("golden_apple", 1)]),
        ],
        # ---- checkpoints: supplies are shared, the armoury belongs to the squad ------------------------------------
        "blockpost_supply": [
            (3, 5, [it("bread", 10, 2, 5), it("cooked_beef", 6, 1, 3), it(d("miners_ration"), 8, 1, 3),
                    it("iron_nugget", 6, 2, 6), it("torch", 8, 3, 8), it("gunpowder", 5, 1, 3),
                    it(d("rifle_cartridge"), 12, 4, 12), it(d("gun_parts"), 3, 1, 2),
                    it(d("rifle_magazine"), 2), it("golden_apple", 1), it(d("miners_token"), 4, 1, 3)]),
        ],
    }
    # ---- 0.3.0: AK modification kits.  One separate pool per chest (1 roll, mostly empty) so that the kits neither
    #      dilute nor replace the rest of the loot.  The more useful a kit, the rarer: barrel (-10 % spread) and
    #      spring (+10 % fire rate) are the most common, then the stabilizer (-20 % spread), then the improved
    #      reload mechanism (-20 % reload time) and the extended magazine (+50 % capacity) is the rarest.
    #      tools/validate.py checks this ordering.
    KIT_WEIGHT = {"barrel": 4, "spring": 4, "stabilizer": 3, "mechanism": 2, "magazine": 1}

    def kit_pool(empty_weight, kinds=("barrel", "spring", "stabilizer", "mechanism", "magazine")):
        return (1, 1, [it(d("ak_mod_" + k), KIT_WEIGHT[k]) for k in kinds] + [empty(empty_weight)])

    tables["factory"].append(kit_pool(36))                                       # 14/50 = 28 % per chest
    tables["mine_deep"].append(kit_pool(47, ("barrel", "spring", "stabilizer", "mechanism")))      # 13/60
    tables["freight_station"].append(kit_pool(49, ("barrel", "spring", "stabilizer")))             # 11/60
    tables["blockpost_supply"].append(kit_pool(46))                              # 14/60 = 23 %
    for faction, prefix in (("north", "steppe"), ("south", "terricone")):
        tables[f"blockpost_armory_{faction}"] = [
            # at most two pieces of the squad's own uniform per chest, never the whole set
            (1, 2, [it(d(prefix + "_helmet"), 4), it(d(prefix + "_jacket"), 3), it(d(prefix + "_trousers"), 3),
                    it(d(prefix + "_boots"), 4), empty(10)]),
            (1, 1, [it(d("ak_rifle"), 3), empty(9)]),
            (2, 3, [it(d("rifle_cartridge"), 12, 6, 16), it(d("rifle_magazine"), 4), it(d("gun_parts"), 3, 1, 2),
                    it("iron_ingot", 5, 1, 3), it("cooked_beef", 4, 1, 3), it(d("coal_plate"), 2, 1, 2),
                    it(d("miners_token"), 3, 1, 3), it("tnt", 1)]),
            kit_pool(26),                                                        # 14/40 = 35 % per armoury chest
        ]
    for name, pools in tables.items():
        wj(os.path.join(DATA, "loot_tables", "chests", name + ".json"), {
            "type": "minecraft:chest", "random_sequence": N + "chests/" + name,
            "pools": [{"rolls": {"type": "minecraft:uniform", "min": float(lo), "max": float(hi)},
                       "bonus_rolls": 0.0, "entries": entries} for lo, hi, entries in pools]})

    # ---- entity loot: ammunition is dropped far more often than parts; the rifle itself is an equipment drop
    #      (chance per rank is set in MilitiaEntity.populateDefaultEquipmentSlots: 4% / 10% / 18%)
    def drop(item, lo, hi, chance, looting=0.05, rank=None):
        conds = [{"condition": "minecraft:random_chance_with_looting", "chance": chance, "looting_multiplier": looting}]
        if rank is not None:
            conds.insert(0, {"condition": "minecraft:entity_properties", "entity": "this",
                             "predicate": {"nbt": "{Rank:%d}" % rank}})
        return {"rolls": 1.0, "bonus_rolls": 0.0, "conditions": conds, "entries": [{
            "type": "minecraft:item", "name": item if ":" in item else "minecraft:" + item,
            "functions": [{"function": "minecraft:set_count",
                           "count": {"type": "minecraft:uniform", "min": float(lo), "max": float(hi)}, "add": False},
                          {"function": "minecraft:looting_enchant", "count": {"min": 0.0, "max": 1.0}}]}]}

    fighter_pools = [
        drop(d("rifle_cartridge"), 1, 3, 0.60, rank=0), drop("iron_nugget", 1, 2, 0.35, rank=0),
        drop("bread", 1, 1, 0.25, rank=0),
        drop(d("rifle_cartridge"), 2, 5, 0.75, rank=1), drop(d("gun_parts"), 1, 1, 0.10, rank=1),
        drop(d("miners_token"), 1, 1, 0.30, rank=1), drop("cooked_beef", 1, 1, 0.20, rank=1),
        drop(d("rifle_cartridge"), 3, 8, 0.90, rank=2), drop(d("gun_parts"), 1, 2, 0.25, rank=2),
        drop(d("rifle_magazine"), 1, 1, 0.15, rank=2), drop(d("coal_plate"), 1, 1, 0.08, rank=2),
        drop(d("miners_token"), 1, 3, 0.55, rank=2),
    ]
    miner_pools = [drop("coal", 0, 2, 0.6), drop("iron_nugget", 0, 2, 0.3), drop(d("miners_token"), 1, 1, 0.15),
                   drop("bread", 1, 1, 0.2)]
    def sure(item, lo, hi):                       # a guaranteed pool (no condition)
        return {"rolls": 1.0, "bonus_rolls": 0.0, "entries": [{
            "type": "minecraft:item", "name": item if ":" in item else "minecraft:" + item,
            "functions": [{"function": "minecraft:set_count",
                           "count": {"type": "minecraft:uniform", "min": float(lo), "max": float(hi)}, "add": False}]}]}

    # the boss: the unique rewards are guaranteed, the rest is generous (it is a long fight)
    boss_pools = [
        sure(d("director_pickaxe"), 1, 1), sure(d("director_badge"), 1, 1),
        sure(d("miners_token"), 16, 32), sure("diamond", 3, 6), sure(d("coal_plate"), 6, 12),
        sure(d("rifle_cartridge"), 32, 64), sure(d("gun_parts"), 2, 4), sure(d("rifle_magazine"), 1, 2),
        drop("enchanted_golden_apple", 1, 1, 0.25, looting=0.0), drop(d("combine_siren"), 1, 1, 0.15, looting=0.0),
    ]
    for name, pools in (("north_fighter", fighter_pools), ("south_fighter", fighter_pools), ("miner", miner_pools),
                        ("combine_director", boss_pools)):
        wj(os.path.join(DATA, "loot_tables", "entities", name + ".json"),
           {"type": "minecraft:entity", "random_sequence": N + "entities/" + name, "pools": pools})


def main():
    # Only clean what this script owns: block loot tables and recipes belong to gen_resources.py.
    for sub in ("worldgen", "dimension", "forge", os.path.join("loot_tables", "chests"),
                os.path.join("loot_tables", "entities"), os.path.join("tags", "worldgen")):
        shutil.rmtree(os.path.join(DATA, sub), ignore_errors=True)
    gen_terrain()
    gen_biomes()
    gen_features()
    gen_processors()
    gen_loot()
    print("worldgen core written (structures are generated by gen_structures.py)")


if __name__ == "__main__":
    main()

"""Builds all structure templates (.nbt) and the worldgen JSON that places them:
template pools, jigsaw structures and structure sets."""
import os
import shutil

import random
import zlib

import structures_admin
import structures_industry
import structures_military
import structures_mines
import structures_town
from gen_worldgen import DATA, WG, wj
from nbt import Tpl
from populate import fighter_nbt, miner_nbt, populate

N = "donbass:"
NBT_DIR = os.path.join(DATA, "structures")


def element(name, processors, weight=1):
    return {"weight": weight, "element": {
        "element_type": "minecraft:single_pool_element", "location": N + name,
        "processors": N + processors if processors else {"processors": []}, "projection": "rigid"}}


def pool(path, elements, fallback="minecraft:empty"):
    wj(os.path.join(WG, "template_pool", path + ".json"), {"fallback": fallback, "elements": elements})


def spawn_overrides(miners=None, fighters=None):
    """Natural spawns inside the structure's pieces. miners / fighters: (min, max) group sizes or None.
    fighters may also be a list of (entity, (min, max)) to restrict a post to one squad."""
    out = {}
    if miners:
        out["creature"] = {"bounding_box": "piece", "spawns": [
            {"type": N + "miner", "weight": 1, "minCount": miners[0], "maxCount": miners[1]}]}
    if fighters:
        spawns = fighters if isinstance(fighters, list) else [
            ("north_fighter", fighters), ("south_fighter", fighters)]
        out["monster"] = {"bounding_box": "piece", "spawns": [
            {"type": N + e, "weight": 1, "minCount": g[0], "maxCount": g[1]} for e, g in spawns]}
    return out


def jigsaw_structure(name, start_pool, size, ground, max_dist, adaptation="beard_thin", overrides=None):
    wj(os.path.join(WG, "structure", name + ".json"), {
        "type": "minecraft:jigsaw", "biomes": "#donbass:has_structures", "step": "surface_structures",
        "start_pool": N + start_pool, "size": size, "max_distance_from_center": max_dist,
        "start_height": {"absolute": -ground}, "project_start_to_heightmap": "WORLD_SURFACE_WG",
        "use_expansion_hack": False, "terrain_adaptation": adaptation, "spawn_overrides": overrides or {}})


def populate_templates(templates):
    """Put the people into the buildings: miners where people work and live, fighters at the checkpoints."""
    placed = {"miner": 0, "fighter": 0}
    for name, (tpl, ground) in templates.items():
        lo, hi = ground + 1, ground + 4
        if name == "mine/active":
            placed["miner"] += populate(tpl, name, [miner_nbt(), miner_nbt()], lo, hi, prefer_work=True)
        elif name in ("industry/steelworks", "industry/coke_plant"):
            placed["miner"] += populate(tpl, name, [miner_nbt(), miner_nbt()], lo, hi, prefer_work=True)
        elif name == "rail/freight_station":
            placed["miner"] += populate(tpl, name, [miner_nbt()], lo, hi)
        elif name.startswith("settlement/center_"):
            placed["miner"] += populate(tpl, name, [miner_nbt()], lo, hi)
        elif name.startswith("settlement/"):
            rng = random.Random(zlib.crc32(("who:" + name).encode()))
            if rng.random() < 0.6:                    # about every second house plot has somebody around
                placed["miner"] += populate(tpl, name, [miner_nbt()], lo, hi)
        elif name.startswith("military/blockpost_"):
            placed["fighter"] += len(tpl.entities)
    return placed


def structure_set(name, salt, spacing, separation, structures, exclusion=None):
    placement = {"type": "minecraft:random_spread", "salt": salt, "spacing": spacing, "separation": separation}
    if exclusion:
        placement["exclusion_zone"] = {"other_set": N + exclusion[0], "chunk_count": exclusion[1]}
    wj(os.path.join(WG, "structure_set", name + ".json"), {
        "placement": placement,
        "structures": [{"structure": N + s, "weight": w} for s, w in structures]})


def main():
    shutil.rmtree(NBT_DIR, ignore_errors=True)
    for sub in ("template_pool", "structure", "structure_set"):
        shutil.rmtree(os.path.join(WG, sub), ignore_errors=True)

    templates = {}
    templates.update(structures_mines.all_templates())
    town, plot_weights = structures_town.all_templates()
    templates.update(town)
    templates.update(structures_industry.all_templates())
    templates.update(structures_military.all_templates())
    templates.update(structures_admin.all_templates())
    people = populate_templates(templates)

    for name, (tpl, ground) in templates.items():
        for (x, y, z) in tpl.blocks:
            sx, sy, sz = tpl.size
            assert 0 <= x < sx and 0 <= y < sy and 0 <= z < sz, f"{name}: block {(x, y, z)} outside {tpl.size}"
        tpl.save(os.path.join(NBT_DIR, name + ".nbt"))
    grounds = {n: g for n, (_, g) in templates.items()}

    # the empty arena of the GameTests (gametest/BossGameTests.java): a flat floor, nothing else. It is not part of
    # any pool, so it never generates in the world; the validator knows it by the "gametest/" prefix.
    arena = Tpl(15, 8, 15)
    arena.fill(0, 0, 0, 14, 0, 14, "minecraft:stone")
    arena.save(os.path.join(NBT_DIR, "gametest", "arena.nbt"))

    # ---- mines: one single-piece structure each, buried so that the yard lands on the surface
    for kind, proc in (("shallow", "abandoned"), ("active", "weathered"), ("deep", "abandoned")):
        pool("mine/" + kind, [element("mine/" + kind, proc)])
        jigsaw_structure(kind + "_mine", "mine/" + kind, 1, grounds["mine/" + kind], 32, "none",
                         spawn_overrides(miners=(1, 2) if kind == "active" else None,
                                         fighters=(1, 2) if kind == "deep" else None))

    # ---- worker settlement
    pool("settlement/centers", [element("settlement/center_monument", "weathered"),
                                element("settlement/center_water_tower", "weathered")])
    pool("settlement/plots", [element(n, "weathered", plot_weights[n]) for n in sorted(plot_weights)])
    jigsaw_structure("miners_settlement", "settlement/centers", 5, 1, 80, overrides=spawn_overrides(miners=(1, 3)))

    # ---- industry: each plant exists in a working and in a ruined version
    for plant in ("steelworks", "coke_plant"):
        pool("industry/" + plant, [element("industry/" + plant, "weathered", 2),
                                   element("industry/" + plant, "ruined", 3)])
        jigsaw_structure(plant, "industry/" + plant, 1, 1, 48,
                         overrides=spawn_overrides(miners=(1, 2), fighters=(1, 2)))

    # ---- railway: station + branch line made of chained track segments, capped by buffer ends
    pool("rail/stations", [element("rail/freight_station", "weathered", 1),
                           element("rail/freight_station", "ruined", 1)])
    pool("rail/line", [element("rail/line_plain", "weathered", 4), element("rail/line_signal", "weathered", 2),
                       element("rail/line_wreck", "ruined", 1), element("rail/line_crossing", "weathered", 2)],
         fallback=N + "rail/ends")
    pool("rail/ends", [element("rail/line_end", "weathered")])
    jigsaw_structure("freight_station", "rail/stations", 5, 1, 96,
                     overrides=spawn_overrides(miners=(1, 1), fighters=(1, 2)))

    # ---- checkpoints of the two squads (a single piece each, garrisoned by template entities)
    for faction in ("north", "south"):
        pool(f"military/blockpost_{faction}", [element(f"military/blockpost_{faction}", "weathered")])
        jigsaw_structure(f"blockpost_{faction}", f"military/blockpost_{faction}", 1, 1, 24, "beard_thin",
                         spawn_overrides(fighters=[(faction + "_fighter", (1, 2))]))

    # ---- the administration building (director's office): rare, no natural spawns, holds the boss siren
    pool("industry/administration", [element("industry/administration", "weathered")])
    jigsaw_structure("administration", "industry/administration", 1, 1, 48, "beard_thin")

    # ---- structure sets (spacing / separation are in chunks)
    structure_set("miners_settlements", 1730101, 16, 6, [("miners_settlement", 1)])
    structure_set("shallow_mines", 1730102, 10, 4, [("shallow_mine", 1)])
    structure_set("active_mines", 1730103, 20, 7, [("active_mine", 1)], exclusion=("miners_settlements", 3))
    structure_set("deep_mines", 1730104, 24, 8, [("deep_mine", 1)], exclusion=("miners_settlements", 3))
    structure_set("industrial_plants", 1730105, 18, 6, [("steelworks", 1), ("coke_plant", 1)],
                  exclusion=("miners_settlements", 4))
    structure_set("freight_stations", 1730106, 22, 7, [("freight_station", 1)], exclusion=("miners_settlements", 4))
    structure_set("blockposts", 1730107, 14, 5, [("blockpost_north", 1), ("blockpost_south", 1)],
                  exclusion=("miners_settlements", 3))

    structure_set("administrations", 1730108, 36, 14, [("administration", 1)], exclusion=("miners_settlements", 4))

    print(f"structures: {len(templates)} templates written to {os.path.relpath(NBT_DIR, DATA)}; "
          f"entities placed: {people['miner']} miners, {people['fighter']} fighters")


if __name__ == "__main__":
    main()

"""Adds miners and fighters to structure templates (template entities, placed when the structure generates).

Entities are spread over valid standing spots of a template: a full block underfoot (no stairs, slabs, fences,
containers, fire...) and two free blocks above.  Everything is seeded, so the result is reproducible.
"""
import random
import zlib

from nbt import AIR, Byte, Tpl

BAD_FLOOR = ("stairs", "slab", "door", "fence", "bars", "pane", "glass", "carpet", "rail", "ladder", "chest", "barrel",
             "campfire", "magma", "lava", "water", "spawner", "bed", "lantern", "torch", "scaffold", "web",
             "trapdoor", "button", "plate", "sign", "banner", "anvil", "furnace", "table", "jigsaw", "wall",
             "air", "smoldering", "bunker", "lamp", "grate", "wheel", "girder", "beam", "ice", "leaves", "grass_block")
WORK_HINTS = ("coal_bunker", "coal_seam", "anthracite", "furnace", "anvil", "mine_lamp", "ventilation")


def miner_nbt():
    return {"id": "donbass:miner", "PersistenceRequired": Byte(1)}


def fighter_nbt(faction, rank):
    return {"id": f"donbass:{faction}_fighter", "PersistenceRequired": Byte(1), "Rank": int(rank)}


def _free(tpl, x, y, z):
    b = tpl.blocks.get((x, y, z))
    return b is None or b[0] == AIR


def standing_spots(tpl, y_lo, y_hi, margin=1):
    sx, sy, sz = tpl.size
    out = []
    for (x, y, z), (name, _props, _nbt) in tpl.blocks.items():
        if any(k in name for k in BAD_FLOOR):
            continue
        sy_pos = y + 1
        if not (y_lo <= sy_pos <= y_hi) or sy_pos + 1 >= sy:
            continue
        if not (margin <= x < sx - margin and margin <= z < sz - margin):
            continue
        if _free(tpl, x, sy_pos, z) and _free(tpl, x, sy_pos + 1, z):
            out.append((x, sy_pos, z))
    return sorted(out)


def _near_work(tpl, spot, radius=3):
    x, y, z = spot
    for (bx, by, bz), (name, _p, _n) in tpl.blocks.items():
        if abs(bx - x) <= radius and abs(bz - z) <= radius and abs(by - y) <= 2 and any(h in name for h in WORK_HINTS):
            return True
    return False


def populate(tpl, name, nbt_list, y_lo, y_hi, prefer_work=False, min_dist=5):
    """Place one entity per NBT in nbt_list on well-separated standing spots (deterministic per template name)."""
    rng = random.Random(zlib.crc32(("pop:" + name).encode()))
    spots = standing_spots(tpl, y_lo, y_hi)
    if not spots:
        raise ValueError(f"{name}: no standing spot for entities in y {y_lo}..{y_hi}")
    rng.shuffle(spots)
    if prefer_work:
        spots.sort(key=lambda s: 0 if _near_work(tpl, s) else 1)
    chosen = []
    for spot in spots:
        if all((spot[0] - c[0]) ** 2 + (spot[2] - c[2]) ** 2 >= min_dist * min_dist for c in chosen):
            chosen.append(spot)
        if len(chosen) == len(nbt_list):
            break
    if len(chosen) < len(nbt_list):          # crowded template: relax the spacing
        for spot in spots:
            if spot not in chosen:
                chosen.append(spot)
            if len(chosen) == len(nbt_list):
                break
    for (x, y, z), nbt in zip(chosen, nbt_list):
        tpl.entity(x + 0.5, y, z + 0.5, nbt)
    return len(chosen)

"""Static validation of the whole mod: JSON syntax, cross references, structure templates
(block ids + properties checked against the vanilla 1.20.1 block table) and Java<->content
consistency.  This is NOT a substitute for running the game - it catches broken references.

Usage: python3 validate.py        (exit code 1 when any error is found)
"""
import glob
import gzip
import json
import os
import re
import struct
import sys

from content import ARMOR_SETS, BLOCKS, ITEMS, LANG_EXTRA, RECIPES

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.normpath(os.path.join(HERE, ".."))
RES = os.path.join(PROJ, "src", "main", "resources")
ASSETS = os.path.join(RES, "assets", "donbass")
DATA = os.path.join(RES, "data", "donbass")
JAVA = os.path.join(PROJ, "src", "main", "java")
REF = os.path.join(HERE, "reference")

errors, warnings = [], []


def err(msg):
    errors.append(msg)


def load(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:  # noqa: BLE001
        err(f"invalid JSON {os.path.relpath(path, PROJ)}: {e}")
        return None


def refj(name):
    with open(os.path.join(REF, name), encoding="utf-8") as f:
        return json.load(f)


VBLOCKS = refj("vanilla_blocks_1.20.1.json")      # only blocks that HAVE properties: id -> [props, default]
for _bid in refj("vanilla_block_ids_1.20.1.json"):  # full registry: property-less blocks (dirt, air, ...)
    VBLOCKS.setdefault(_bid, [{}, {}])
VITEMS = set(refj("vanilla_items_1.20.1.json"))
VWG = refj("vanilla_worldgen_names_1.20.1.json")

# ---- property tables for our own blocks, derived from the block kind ----------
BOOL = ["true", "false"]
FACING4 = ["north", "south", "west", "east"]
KIND_PROPS = {
    "cube": {}, "falling": {}, "magma": {}, "glass": {}, "workbench": {},
    "pillar": {"axis": ["x", "y", "z"]},
    "slab": {"type": ["top", "bottom", "double"], "waterlogged": BOOL},
    "stairs": {"facing": FACING4, "half": ["top", "bottom"],
               "shape": ["straight", "inner_left", "inner_right", "outer_left", "outer_right"], "waterlogged": BOOL},
    "pane": {"north": BOOL, "south": BOOL, "east": BOOL, "west": BOOL, "waterlogged": BOOL},
}
OWN_BLOCKS = {b["id"]: KIND_PROPS[b["kind"]] for b in BLOCKS}
OWN_ITEM_IDS = {i["id"] for i in ITEMS} | set(OWN_BLOCKS)
VANILLA_BLOCK_IDS = set(VBLOCKS)


def java_text(rel):
    return open(os.path.join(JAVA, "com/donbass/mod", rel), encoding="utf-8").read()


def registered_entities():
    return set(re.findall(r'ENTITIES\.register\("([a-z_]+)"', java_text("registry/ModEntities.java")))


def registered_sounds():
    return set(re.findall(r'register\("([a-z0-9_.]+)"\)', java_text("registry/ModSounds.java")))


def armor_material_names():
    return re.findall(r'^\s+[A-Z_]+\("([a-z_]+)",', java_text("registry/ModArmorMaterials.java"), flags=re.M)


def item_exists(ref_id):
    ns, _, name = ref_id.rpartition(":") if ":" in ref_id else ("minecraft", "", ref_id)
    ns = ns or "minecraft"
    return name in OWN_ITEM_IDS if ns == "donbass" else name in VITEMS


# ---- minimal NBT reader -------------------------------------------------------
def read_nbt(buf, off, tid):
    if tid == 1:
        return struct.unpack_from(">b", buf, off)[0], off + 1
    if tid == 2:
        return struct.unpack_from(">h", buf, off)[0], off + 2
    if tid == 3:
        return struct.unpack_from(">i", buf, off)[0], off + 4
    if tid == 4:
        return struct.unpack_from(">q", buf, off)[0], off + 8
    if tid == 5:
        return struct.unpack_from(">f", buf, off)[0], off + 4
    if tid == 6:
        return struct.unpack_from(">d", buf, off)[0], off + 8
    if tid == 8:
        n = struct.unpack_from(">H", buf, off)[0]
        return buf[off + 2:off + 2 + n].decode("utf-8"), off + 2 + n
    if tid == 9:
        et, n = struct.unpack_from(">bi", buf, off)
        off += 5
        out = []
        for _ in range(n):
            v, off = read_nbt(buf, off, et)
            out.append(v)
        return out, off
    if tid == 10:
        d = {}
        while True:
            et = buf[off]
            off += 1
            if et == 0:
                return d, off
            n = struct.unpack_from(">H", buf, off)[0]
            key = buf[off + 2:off + 2 + n].decode("utf-8")
            off += 2 + n
            d[key], off = read_nbt(buf, off, et)
    raise ValueError(f"unsupported NBT tag {tid}")


def read_template(path):
    raw = gzip.open(path).read()
    assert raw[0] == 10, "root is not a compound"
    n = struct.unpack_from(">H", raw, 1)[0]
    root, _ = read_nbt(raw, 3 + n, 10)
    return root


# ---- checks -------------------------------------------------------------------
def check_templates():
    pools = {os.path.relpath(p, os.path.join(DATA, "worldgen", "template_pool"))[:-5].replace(os.sep, "/")
             for p in glob.glob(os.path.join(DATA, "worldgen", "template_pool", "**", "*.json"), recursive=True)}
    loot = {os.path.relpath(p, os.path.join(DATA, "loot_tables"))[:-5].replace(os.sep, "/")
            for p in glob.glob(os.path.join(DATA, "loot_tables", "**", "*.json"), recursive=True)}
    count = blocks_checked = n_entities = 0
    for path in sorted(glob.glob(os.path.join(DATA, "structures", "**", "*.nbt"), recursive=True)):
        rel = os.path.relpath(path, os.path.join(DATA, "structures"))
        count += 1
        try:
            t = read_template(path)
        except Exception as e:  # noqa: BLE001
            err(f"{rel}: unreadable NBT ({e})")
            continue
        sx, sy, sz = t["size"]
        if t.get("DataVersion") != 3465:
            err(f"{rel}: DataVersion {t.get('DataVersion')} != 3465 (1.20.1)")
        palette = t["palette"]
        for i, entry in enumerate(palette):
            name = entry["Name"]
            ns, _, bid = name.partition(":")
            props = entry.get("Properties", {})
            allowed = OWN_BLOCKS.get(bid) if ns == "donbass" else (VBLOCKS[bid][0] if bid in VBLOCKS else None)
            if allowed is None:
                err(f"{rel}: unknown block {name}")
                continue
            for k, v in props.items():
                if k not in allowed:
                    err(f"{rel}: {name} has no property '{k}'")
                else:
                    ok = allowed[k] if isinstance(allowed[k], list) else [allowed[k]]
                    if v not in [str(x) for x in ok]:
                        err(f"{rel}: {name}[{k}={v}] not in {ok}")
        for b in t["blocks"]:
            blocks_checked += 1
            x, y, z = b["pos"]
            if not (0 <= x < sx and 0 <= y < sy and 0 <= z < sz):
                err(f"{rel}: block at {b['pos']} outside size {t['size']}")
            if b["state"] >= len(palette):
                err(f"{rel}: state index {b['state']} out of palette")
            nbt = b.get("nbt")
            if not nbt:
                continue
            if "LootTable" in nbt:
                lt = nbt["LootTable"].replace("donbass:", "")
                if lt not in loot:
                    err(f"{rel}: loot table {nbt['LootTable']} does not exist")
            if nbt.get("id") == "minecraft:jigsaw":
                p = nbt["pool"]
                if p != "minecraft:empty" and p.replace("donbass:", "") not in pools:
                    err(f"{rel}: jigsaw pool {p} does not exist")
                if nbt["name"] != nbt["target"]:
                    warnings.append(f"{rel}: jigsaw name != target ({nbt['name']} / {nbt['target']})")
        entities_total = check_template_entities(rel, t, sx, sy, sz)
        n_entities += entities_total
    print(f"  templates: {count} files, {blocks_checked} blocks, {n_entities} entities checked")


def check_template_entities(rel, t, sx, sy, sz):
    """Entities stored in a template: known id, inside the box, not embedded in a block, has two free blocks above."""
    known = {"donbass:" + e for e in registered_entities()}
    solid = {}
    for b in t["blocks"]:
        solid[tuple(b["pos"])] = t["palette"][b["state"]]["Name"]
    for e in t.get("entities", []):
        nbt = e["nbt"]
        eid = nbt.get("id")
        if eid not in known:
            err(f"{rel}: entity {eid} is not a registered Donbass entity")
        x, y, z = e["pos"]
        bx, by, bz = e["blockPos"]
        if not (0 <= x < sx and 0 <= y < sy and 0 <= z < sz):
            err(f"{rel}: entity {eid} at {e['pos']} outside the template")
            continue
        for dy in (0, 1):
            name = solid.get((bx, by + dy, bz))
            if name is not None and name != "minecraft:air":
                err(f"{rel}: entity {eid} at {e['blockPos']} is inside {name}")
        below = solid.get((bx, by - 1, bz))
        if below is None or below == "minecraft:air":
            warnings.append(f"{rel}: entity {eid} at {e['blockPos']} has no block of the template underfoot")
        if "fighter" in str(eid) and nbt.get("Rank") not in (None, 0, 1, 2):
            err(f"{rel}: fighter with rank {nbt.get('Rank')}")
        if nbt.get("PersistenceRequired") != 1:
            warnings.append(f"{rel}: {eid} may despawn (PersistenceRequired missing)")
    return len(t.get("entities", []))


def check_sounds_and_gear():
    """sounds.json <-> ModSounds <-> ogg files, armour layer textures, entity skins."""
    snd = load(os.path.join(ASSETS, "sounds.json")) or {}
    names = registered_sounds()
    if set(snd) != names:
        err(f"sounds.json events {sorted(set(snd) ^ names)} differ from ModSounds.java")
    for event, spec in snd.items():
        for ref in spec["sounds"]:
            ref = ref["name"] if isinstance(ref, dict) else ref        # long tracks are {"name": ..., "stream": true}
            f = os.path.join(ASSETS, "sounds", ref.split(":")[1] + ".ogg")
            if not os.path.isfile(f):
                err(f"sound {event}: file {os.path.relpath(f, ASSETS)} missing")
            elif open(f, "rb").read(4) != b"OggS":
                err(f"sound {event}: {os.path.basename(f)} is not an OGG file")
    mats = armor_material_names()
    expected = {m.lower() for m in ARMOR_SETS}
    if set(mats) != expected:
        err(f"ModArmorMaterials names {sorted(mats)} != content.py sets {sorted(expected)}")
    for m in mats:
        for layer in (1, 2):
            f = os.path.join(ASSETS, "textures", "models", "armor", f"{m}_layer_{layer}.png")
            if not os.path.isfile(f):
                err(f"missing armour texture {os.path.relpath(f, ASSETS)}")
    def png_size(path):                      # stdlib only: the CI runner has no Pillow
        with open(path, "rb") as fh:
            head = fh.read(24)
        if head[:8] != b"\x89PNG\r\n\x1a\n" or head[12:16] != b"IHDR":
            return None
        return struct.unpack(">II", head[16:24])

    for m in mats:
        for layer in (1, 2):
            f = os.path.join(ASSETS, "textures", "models", "armor", f"{m}_layer_{layer}.png")
            if os.path.isfile(f) and png_size(f) != (64, 32):
                err(f"{os.path.basename(f)} must be 64x32")
    for e in registered_entities():
        f = os.path.join(ASSETS, "textures", "entity", e + ".png")
        if not os.path.isfile(f):
            err(f"missing entity skin {e}")
        elif png_size(f) != (64, 64):
            err(f"entity skin {e} must be 64x64")
        if not os.path.isfile(os.path.join(DATA, "loot_tables", "entities", e + ".json")):
            err(f"missing entity loot table {e}")
        if f"entity.donbass.{e}" not in LANG_EXTRA:
            err(f"missing lang key entity.donbass.{e}")
    # structure spawn overrides must name registered entities
    for p in glob.glob(os.path.join(DATA, "worldgen", "structure", "*.json")):
        d = load(p) or {}
        for cat, spec in d.get("spawn_overrides", {}).items():
            for sp in spec["spawns"]:
                if sp["type"].replace("donbass:", "") not in registered_entities():
                    err(f"{os.path.basename(p)}: spawn override {sp['type']} is not a Donbass entity")
                if sp["minCount"] > sp["maxCount"]:
                    err(f"{os.path.basename(p)}: minCount > maxCount")
    # the boss: summoned only (no spawn overrides, no spawn placement, no spawn egg), music loops match the code
    for p in glob.glob(os.path.join(DATA, "worldgen", "structure", "*.json")):
        d = load(p) or {}
        for spec in d.get("spawn_overrides", {}).values():
            if any("combine_director" in sp["type"] for sp in spec["spawns"]):
                err(f"{os.path.basename(p)}: the boss must never spawn naturally")
    if "COMBINE_DIRECTOR" in java_text("event/ModEntityEvents.java").split("onSpawnPlacements")[-1]:
        err("ModEntityEvents registers a spawn placement for the boss")
    if any(i.get("entity") == "COMBINE_DIRECTOR" for i in ITEMS):
        err("the boss must not have a spawn egg")
    boss_src = java_text("entity/CombineDirectorEntity.java")
    m = re.search(r"MUSIC_LOOP_TICKS\s*=\s*(\d+)", boss_src)
    secs = re.search(r"^MUSIC_SECONDS\s*=\s*([\d.]+)", open(os.path.join(HERE, "gen_sounds.py"), encoding="utf-8").read(),
                     flags=re.M)
    if not m or not secs or int(m.group(1)) != int(float(secs.group(1)) * 20):
        err("CombineDirectorEntity.MUSIC_LOOP_TICKS does not match gen_sounds.MUSIC_SECONDS")
    siren_loot = load(os.path.join(DATA, "loot_tables", "chests", "director_office.json")) or {}
    if "combine_siren" not in json.dumps(siren_loot):
        err("director_office loot table does not contain the siren")
    print(f"  gear: {len(snd)} sound events, {len(mats)} armour materials, {len(registered_entities())} entities")


def check_assets():
    n_models = 0
    for b in BLOCKS:
        i = b["id"]
        if not os.path.isfile(os.path.join(ASSETS, "blockstates", i + ".json")):
            err(f"missing blockstate {i}")
        if not os.path.isfile(os.path.join(ASSETS, "models", "item", i + ".json")):
            err(f"missing item model for block {i}")
        if not os.path.isfile(os.path.join(DATA, "loot_tables", "blocks", i + ".json")):
            err(f"missing loot table {i}")
    for it in ITEMS:
        if not os.path.isfile(os.path.join(ASSETS, "models", "item", it["id"] + ".json")):
            err(f"missing item model {it['id']}")
        # spawn eggs use minecraft:item/template_spawn_egg (tinted by colour), so they have no own texture
        if it["kind"] != "egg" and not os.path.isfile(os.path.join(ASSETS, "textures", "item", it["id"] + ".png")):
            err(f"missing item texture {it['id']}")

    def model_exists(ref_id):
        ns, _, p = ref_id.partition(":")
        if ns == "minecraft":
            return True  # vanilla parents (cube_all, slab, stairs, ...) are not validated here
        return os.path.isfile(os.path.join(ASSETS, "models", p + ".json"))

    for p in glob.glob(os.path.join(ASSETS, "blockstates", "*.json")):
        d = load(p)
        if d is None:
            continue
        entries = list((d.get("variants") or {}).values())
        for part in d.get("multipart", []):
            entries.append(part["apply"])
        for e in entries:
            for m in ([e] if isinstance(e, dict) else e):
                if not model_exists(m["model"]):
                    err(f"{os.path.basename(p)}: model {m['model']} missing")
    for p in glob.glob(os.path.join(ASSETS, "models", "**", "*.json"), recursive=True):
        n_models += 1
        d = load(p)
        if d is None:
            continue
        if "parent" in d and not model_exists(d["parent"]):
            err(f"{os.path.relpath(p, ASSETS)}: parent {d['parent']} missing")
        for key, tex in d.get("textures", {}).items():
            if tex.startswith("donbass:"):
                if not os.path.isfile(os.path.join(ASSETS, "textures", tex[8:] + ".png")):
                    err(f"{os.path.relpath(p, ASSETS)}: texture {tex} missing")
    # every texture file should be used (catch typos / dead files)
    used = set()
    for p in glob.glob(os.path.join(ASSETS, "models", "**", "*.json"), recursive=True):
        for tex in (load(p) or {}).get("textures", {}).values():
            if tex.startswith("donbass:"):
                used.add(tex[8:])
    for p in glob.glob(os.path.join(ASSETS, "textures", "**", "*.png"), recursive=True):
        rel = os.path.relpath(p, os.path.join(ASSETS, "textures"))[:-4].replace(os.sep, "/")
        if rel not in used and not rel.startswith(("models/armor/", "entity/")):
            warnings.append(f"texture {rel} is not referenced by any model")
    print(f"  assets: {len(BLOCKS)} blocks, {len(ITEMS)} items, {n_models} models")


def check_rifle_model():
    """The AK must stay a real 3D model with identity-like hand transforms (0.2.0 used a flat sprite with the
    crossbow's Rx(-90) transforms, which laid the rifle on its side). See docs/AK_ORIENTATION.md."""
    path = os.path.join(ASSETS, "models", "item", "ak_rifle.json")
    d = load(path)
    if d is None:
        return
    if not d.get("elements"):
        err("ak_rifle.json: no 'elements': the rifle must be a 3D model (a flat sprite is edge-on in the hands)")
        return
    if d.get("parent", "").endswith("generated") or d.get("parent", "").endswith("handheld"):
        err("ak_rifle.json: parent item/generated / handheld would turn it into a flat sprite again")
    for key in ("thirdperson_righthand", "thirdperson_lefthand", "firstperson_righthand", "firstperson_lefthand"):
        t = (d.get("display") or {}).get(key)
        if not t:
            err(f"ak_rifle.json: display.{key} missing")
            continue
        rx, ry, rz = t.get("rotation", [0, 0, 0])
        if rx != 0 or rz != 0 or abs(ry) > 20:
            err(f"ak_rifle.json: display.{key}.rotation {t.get('rotation')}: the model's barrel is -z, so a hand "
                "transform may only yaw it by a few degrees (a big x/z rotation lays the rifle on its side)")
    for key in ("gui", "ground", "fixed"):
        if key not in (d.get("display") or {}):
            err(f"ak_rifle.json: display.{key} missing")
    tex_ref = d.get("textures", {}).get("0", "")
    tex = os.path.join(ASSETS, "textures", tex_ref[8:] + ".png") if tex_ref.startswith("donbass:") else None
    if not tex or not os.path.isfile(tex):
        err(f"ak_rifle.json: texture {tex_ref} missing")
    for el in d["elements"]:
        for face in el["faces"].values():
            if face.get("texture") != "#0" or not all(0 <= u <= 16 for u in face["uv"]):
                err(f"ak_rifle.json: element {el.get('name')}: bad face {face}")
        for a, b in zip(el["from"], el["to"]):
            if not (-16 <= a <= 32 and -16 <= b <= 32 and a <= b):
                err(f"ak_rifle.json: element {el.get('name')}: from/to {el['from']}/{el['to']} out of range")
        rot = el.get("rotation")
        if rot and rot["angle"] not in (-45, -22.5, 0, 22.5, 45):
            err(f"ak_rifle.json: element {el.get('name')}: rotation angle {rot['angle']} not allowed by the model format")
    # the muzzle must be at the front (-z), the stock at the back
    zs = {e["name"]: (e["from"][2] + e["to"][2]) / 2 for e in d["elements"]}
    if not (zs["muzzle_brake"] < zs["receiver"] < zs["butt_plate"]):
        err("ak_rifle.json: barrel / receiver / stock are not ordered front-to-back along -z")
    ys = {e["name"]: (e["from"][1] + e["to"][1]) / 2 for e in d["elements"]}
    if not (ys["magazine"] < ys["receiver"] < ys["rear_sight"]):
        err("ak_rifle.json: magazine / receiver / sights are not ordered bottom-to-top")
    print("  rifle model: 3D, barrel -z, magazine below, hand transforms near identity")


def check_lang():
    from gen_sounds import lang_entries
    expected = ({f"block.donbass.{b['id']}" for b in BLOCKS} | {f"item.donbass.{i['id']}" for i in ITEMS}
                | set(LANG_EXTRA) | set(lang_entries()))
    for code in ("en_us", "ru_ru", "pl_pl"):
        d = load(os.path.join(ASSETS, "lang", code + ".json"))
        if d is None:
            continue
        if set(d) != expected:
            err(f"lang {code}: missing {sorted(expected - set(d))[:5]} extra {sorted(set(d) - expected)[:5]}")
        for k, v in d.items():
            if not v.strip():
                err(f"lang {code}: empty value for {k}")
    ru = load(os.path.join(ASSETS, "lang", "ru_ru.json")) or {}
    en = load(os.path.join(ASSETS, "lang", "en_us.json")) or {}
    same = [k for k in ru if ru[k] == en.get(k) and k.startswith(("block.", "item."))]
    if same:
        warnings.append(f"lang ru_ru identical to en_us for {len(same)} entries, e.g. {same[:3]}")
    print("  lang: en_us, ru_ru, pl_pl")


def check_recipes_and_loot():
    n = 0
    for p in glob.glob(os.path.join(DATA, "recipes", "*.json")):
        d = load(p)
        if d is None:
            continue
        n += 1
        result = d["result"]["item"] if isinstance(d["result"], dict) else d["result"]
        refs = [result]
        for ing in d.get("ingredients", []) + list(d.get("key", {}).values()):
            if "item" in ing:
                refs.append(ing["item"])
            elif not ing.get("tag"):
                err(f"recipe {os.path.basename(p)}: ingredient without item or tag")
        if "ingredient" in d:
            refs.append(d["ingredient"]["item"])
        for r in refs:
            if not item_exists(r):
                err(f"recipe {os.path.basename(p)}: unknown item {r}")
        if d["type"] == "minecraft:crafting_shaped":
            used = set("".join(d["pattern"])) - {" "}
            if used != set(d["key"]):
                err(f"recipe {os.path.basename(p)}: pattern keys {sorted(used)} != key {sorted(d['key'])}")
    for p in glob.glob(os.path.join(DATA, "loot_tables", "**", "*.json"), recursive=True):
        txt = open(p, encoding="utf-8").read()
        d = load(p)
        if d is None:
            continue
        for m in re.finditer(r'"name":\s*"([a-z_]+:[a-z_/]+)"', txt):
            if not item_exists(m.group(1)):
                err(f"loot {os.path.relpath(p, DATA)}: unknown item {m.group(1)}")
    print(f"  recipes: {n}")


def jid(path, base):
    return os.path.relpath(path, base)[:-5].replace(os.sep, "/")


def check_worldgen():
    wg = os.path.join(DATA, "worldgen")
    have = {}
    for sub in ("biome", "configured_carver", "configured_feature", "placed_feature", "noise_settings",
                "density_function", "processor_list", "structure", "structure_set", "template_pool"):
        have[sub] = {jid(p, os.path.join(wg, sub)) for p in
                     glob.glob(os.path.join(wg, sub, "**", "*.json"), recursive=True)}
    for p in glob.glob(os.path.join(DATA, "**", "*.json"), recursive=True):
        load(p)  # syntax of everything

    def has(kind, ref_id, vanilla_key=None):
        ns, _, name = ref_id.partition(":")
        if ns == "donbass":
            return name in have[kind]
        return vanilla_key is None or name in VWG.get(vanilla_key, [])

    for b in ("steppe", "balka"):
        d = load(os.path.join(wg, "biome", b + ".json")) or {"features": [], "carvers": {}}
        if len(d["features"]) != 11:
            err(f"biome {b}: {len(d['features'])} feature steps (need 11)")
        for step in d["features"]:
            for f in step:
                if not has("placed_feature", f, "placed_feature"):
                    err(f"biome {b}: unknown placed feature {f}")
        for c in d["carvers"].get("air", []):
            if not has("configured_carver", c, "configured_carver"):
                err(f"biome {b}: unknown carver {c}")
    for name in have["placed_feature"]:
        d = load(os.path.join(wg, "placed_feature", name + ".json"))
        if d and not has("configured_feature", d["feature"]):
            err(f"placed_feature {name}: unknown configured feature {d['feature']}")
    java_features = set(re.findall(r'FEATURES\.register\("([a-z_]+)"', open(
        os.path.join(JAVA, "com/donbass/mod/registry/ModFeatures.java"), encoding="utf-8").read()))
    for name in have["configured_feature"]:
        d = load(os.path.join(wg, "configured_feature", name + ".json"))
        if d and d["type"].startswith("donbass:") and d["type"][8:] not in java_features:
            err(f"configured_feature {name}: type {d['type']} is not registered in Java ({java_features})")
        if d and d["type"] == "minecraft:ore":
            for tgt in d["config"]["targets"]:
                bid = tgt["state"]["Name"]
                ns, _, n = bid.partition(":")
                if (ns == "donbass" and n not in OWN_BLOCKS) or (ns == "minecraft" and n not in VBLOCKS):
                    err(f"configured_feature {name}: unknown block {bid}")
    for name in have["structure"]:
        d = load(os.path.join(wg, "structure", name + ".json"))
        if d and not has("template_pool", d["start_pool"]):
            err(f"structure {name}: unknown start pool {d['start_pool']}")
    structures_in_sets = set()
    for name in have["structure_set"]:
        d = load(os.path.join(wg, "structure_set", name + ".json"))
        if not d:
            continue
        pl = d["placement"]
        if pl["separation"] >= pl["spacing"]:
            err(f"structure_set {name}: separation must be < spacing")
        if "exclusion_zone" in pl and not has("structure_set", pl["exclusion_zone"]["other_set"]):
            err(f"structure_set {name}: unknown exclusion set")
        for s in d["structures"]:
            structures_in_sets.add(s["structure"][8:])
            if not has("structure", s["structure"]):
                err(f"structure_set {name}: unknown structure {s['structure']}")
    for name in have["structure"] - structures_in_sets:
        err(f"structure {name} is not part of any structure_set (it would never generate)")
    templates = {jid(p, os.path.join(DATA, "structures")) for p in
                 glob.glob(os.path.join(DATA, "structures", "**", "*.nbt"), recursive=True) if True} if False else {
        os.path.relpath(p, os.path.join(DATA, "structures"))[:-4].replace(os.sep, "/")
        for p in glob.glob(os.path.join(DATA, "structures", "**", "*.nbt"), recursive=True)}
    used_templates = set()
    for name in have["template_pool"]:
        d = load(os.path.join(wg, "template_pool", name + ".json"))
        if not d:
            continue
        if d["fallback"] != "minecraft:empty" and not has("template_pool", d["fallback"]):
            err(f"pool {name}: unknown fallback {d['fallback']}")
        for e in d["elements"]:
            el = e["element"]
            loc = el["location"]
            used_templates.add(loc[8:])
            if loc[8:] not in templates:
                err(f"pool {name}: template {loc} missing")
            proc = el["processors"]
            if isinstance(proc, str) and not has("processor_list", proc, "processor_list"):
                err(f"pool {name}: unknown processor list {proc}")
    for t in templates - used_templates:
        if t.startswith("gametest/"):               # test arenas are loaded by name by the GameTests, not by a pool
            continue
        warnings.append(f"template {t} is not used by any pool")
    for name in have["processor_list"]:
        d = load(os.path.join(wg, "processor_list", name + ".json"))
        for proc in (d or {}).get("processors", []):
            for r in proc.get("rules", []):
                for ref_id in (r["input_predicate"]["block"], r["output_state"]["Name"]):
                    ns, _, n = ref_id.partition(":")
                    if (ns == "donbass" and n not in OWN_BLOCKS) or (ns == "minecraft" and n not in VBLOCKS):
                        err(f"processor {name}: unknown block {ref_id}")
    ns_ = load(os.path.join(wg, "noise_settings", "steppe.json"))
    dens = load(os.path.join(wg, "density_function", "steppe", "base.json"))
    if ns_ is not None and not has("density_function", ns_["noise_router"]["final_density"]["argument"]):
        err("noise_settings steppe: unknown density function")
    for m in re.finditer(r'"noise":\s*"minecraft:([a-z_]+)"', json.dumps(dens) + json.dumps(ns_)):
        if m.group(1) not in VWG["noise"]:
            err(f"unknown vanilla noise minecraft:{m.group(1)}")
    dim = load(os.path.join(DATA, "dimension", "donbass.json"))
    if dim:
        if not has("noise_settings", dim["generator"]["settings"]):
            err("dimension: unknown noise settings")
        for e in dim["generator"]["biome_source"]["biomes"]:
            if not has("biome", e["biome"]):
                err(f"dimension: unknown biome {e['biome']}")
    for tag in glob.glob(os.path.join(DATA, "tags", "worldgen", "biome", "*.json")):
        for v in (load(tag) or {}).get("values", []):
            if not has("biome", v):
                err(f"tag {os.path.basename(tag)}: unknown biome {v}")
    print(f"  worldgen: {sum(len(v) for v in have.values())} JSON files, {len(templates)} templates")


def check_java():
    reg = open(os.path.join(JAVA, "com/donbass/mod/registry/ModBlocks.java"), encoding="utf-8").read()
    defined_blocks = set(re.findall(r"RegistryObject<Block> ([A-Z_]+) =", reg))
    items_src = open(os.path.join(JAVA, "com/donbass/mod/registry/ModItems.java"), encoding="utf-8").read()
    defined_items = set(re.findall(r"RegistryObject<Item> ([A-Z_]+) =", items_src))
    if defined_blocks != {b["id"].upper() for b in BLOCKS}:
        err("ModBlocks.java is out of date - rerun gen_resources.py")
    if defined_items != {i["id"].upper() for i in ITEMS}:
        err("ModItems.java is out of date - rerun gen_resources.py")
    for p in glob.glob(os.path.join(JAVA, "**", "*.java"), recursive=True):
        src = open(p, encoding="utf-8").read()
        for m in re.finditer(r"ModBlocks\.([A-Z_]+)\b", src):
            if m.group(1) not in defined_blocks and m.group(1) not in ("BLOCKS",):
                err(f"{os.path.basename(p)}: ModBlocks.{m.group(1)} does not exist")
        for m in re.finditer(r"ModItems\.([A-Z_]+)\b", src):
            if m.group(1) not in defined_items and m.group(1) not in ("ITEMS",):
                err(f"{os.path.basename(p)}: ModItems.{m.group(1)} does not exist")
    ent_src = java_text("registry/ModEntities.java")
    defined_entities = set(re.findall(r"RegistryObject<EntityType<\w+>> ([A-Z_]+) =", ent_src))
    snd_src = java_text("registry/ModSounds.java")
    defined_sounds = set(re.findall(r"RegistryObject<SoundEvent> ([A-Z_]+) =", snd_src))
    mat_src = java_text("registry/ModArmorMaterials.java")
    defined_mats = set(re.findall(r"^\s+([A-Z_]+)\(\"", mat_src, flags=re.M))
    for p in glob.glob(os.path.join(JAVA, "**", "*.java"), recursive=True):
        src = open(p, encoding="utf-8").read()
        for cls, defined in (("ModEntities", defined_entities), ("ModSounds", defined_sounds),
                             ("ModArmorMaterials", defined_mats)):
            for m in re.finditer(cls + r"\.([A-Z_]+)\b", src):
                if m.group(1) not in defined and m.group(1) not in ("ENTITIES", "SOUNDS", "values", "valueOf"):
                    err(f"{os.path.basename(p)}: {cls}.{m.group(1)} does not exist")
    for it in ITEMS:
        if it["kind"] == "egg" and it["entity"] not in defined_entities:
            err(f"spawn egg {it['id']}: ModEntities.{it['entity']} does not exist")
        if it["kind"] == "armor" and it["mat"] not in defined_mats:
            err(f"armour {it['id']}: ModArmorMaterials.{it['mat']} does not exist")
    mods_toml = open(os.path.join(RES, "META-INF", "mods.toml"), encoding="utf-8").read()
    if 'modId="${mod_id}"' not in mods_toml:
        err("mods.toml: modId placeholder missing")
    print(f"  java: {len(defined_blocks)} block + {len(defined_items)} item registrations match content.py")


JAVA_LANG = {"String", "Math", "Override", "Object", "Integer", "Double", "Float", "Long", "Boolean", "Byte",
             "Short", "Character", "Number", "Class", "Exception", "RuntimeException", "IllegalArgumentException",
             "IllegalStateException", "Iterable", "Runnable", "Deprecated", "SuppressWarnings", "FunctionalInterface",
             "Void", "System", "Thread", "Enum", "Record", "SafeVarargs", "CharSequence", "Comparable", "Error"}


def check_java_imports():
    """Heuristic stand-in for the compiler's 'cannot find symbol' on types: every CamelCase type name
    used in a file must be imported, declared in the file, in the same package, or in java.lang."""
    files = glob.glob(os.path.join(JAVA, "**", "*.java"), recursive=True)
    by_pkg = {}
    for p in files:
        by_pkg.setdefault(os.path.dirname(p), set()).add(os.path.basename(p)[:-5])
    for p in files:
        src = open(p, encoding="utf-8").read()
        body = re.sub(r"//[^\n]*|/\*.*?\*/", " ", src, flags=re.S)
        body = re.sub(r'"(?:\\.|[^"\\])*"', '""', body)
        imported = set(re.findall(r"^import\s+(?:static\s+)?[\w.]*\.(\w+);", body, flags=re.M))
        declared = set(re.findall(r"\b(?:class|interface|enum|record)\s+(\w+)", body))
        body_wo_imports = re.sub(r"^(?:import|package)\s[^;]*;", "", body, flags=re.M)
        used = {m.group(1) for m in re.finditer(r"(?<![\w.])([A-Z][a-z][A-Za-z0-9]*)\b", body_wo_imports)}
        generic = {m for m in used if len(m) == 1}
        for name in sorted(used - imported - declared - by_pkg[os.path.dirname(p)] - JAVA_LANG - generic):
            err(f"{os.path.relpath(p, JAVA)}: type '{name}' is not imported/declared (compile error)")
        for name in sorted(imported):                       # unused imports are only a warning
            if not re.search(r"\b" + name + r"\b", body_wo_imports):
                warnings.append(f"{os.path.relpath(p, JAVA)}: unused import {name}")
        pkg = re.search(r"^package\s+([\w.]+);", body, flags=re.M).group(1)
        expected = os.path.relpath(os.path.dirname(p), JAVA).replace(os.sep, ".")
        if pkg != expected:
            err(f"{os.path.relpath(p, JAVA)}: package {pkg} does not match directory {expected}")
    print(f"  java imports: {len(files)} files checked")


def method_body(src, signature_regex):
    """Text of the first method whose declaration matches the regex (brace matching, strings/comments not special)."""
    m = re.search(signature_regex, src)
    if not m:
        return None
    i = src.index("{", m.end() - 1 if src[m.end() - 1] == "{" else m.end())
    depth, j = 0, i
    while j < len(src):
        if src[j] == "{":
            depth += 1
        elif src[j] == "}":
            depth -= 1
            if depth == 0:
                return src[i:j + 1]
        j += 1
    return None


def check_boss():
    """Regression guards for the 0.2.0 bug 'the boss takes no damage from phase 2 on'.
    Cause: the phase-change lock was an isImmobile() override. LivingEntity.aiStep() skips serverAiStep() for an
    immobile entity, so the timers counted down in customServerAiStep() never ran out and hurt() (which refuses
    damage during the lock) refused it for ever."""
    mod_dir = os.path.join(JAVA, "com", "donbass", "mod")
    ent_dir = os.path.join(mod_dir, "entity")
    for p in glob.glob(os.path.join(ent_dir, "**", "*.java"), recursive=True):
        src = open(p, encoding="utf-8").read()
        body = re.sub(r"//[^\n]*|/\*.*?\*/", " ", src, flags=re.S)
        if re.search(r"boolean\s+isImmobile\s*\(", body):
            err(f"{os.path.relpath(p, JAVA)}: overrides isImmobile(): it switches the AI step off (the boss freeze / "
                "invulnerability bug of 0.2.0). Use a plain flag and handle it in customServerAiStep()/goals")
    path = os.path.join(ent_dir, "CombineDirectorEntity.java")
    src = re.sub(r"//[^\n]*|/\*.*?\*/", " ", open(path, encoding="utf-8").read(), flags=re.S)
    hurt = method_body(src, r"public\s+boolean\s+hurt\s*\(")
    if hurt is None:
        err("CombineDirectorEntity: hurt() override not found")
    else:
        if re.search(r"getPhase|phase", hurt):
            err("CombineDirectorEntity.hurt() depends on the phase: damage rules must not differ between phases")
        if not re.search(r"transition\s*>\s*0", hurt):
            err("CombineDirectorEntity.hurt(): the only allowed refusal is the short phase-change roar (transition > 0)")
    tick = method_body(src, r"public\s+void\s+tick\s*\(")
    if tick is None or "tickTransition" not in tick:
        err("CombineDirectorEntity: the roar countdown (tickTransition) must run from tick(), not from the AI step")
    ai = method_body(src, r"void\s+customServerAiStep\s*\(")
    if ai is not None and "tickTransition" in ai:
        err("CombineDirectorEntity: tickTransition() must not be called from customServerAiStep()")
    if not re.search(r"Attributes\.ARMOR\s*,\s*0\.0D", src):
        err("CombineDirectorEntity: base ARMOR must be 0 (the coal armour it wears already gives 15)")
    test = os.path.join(mod_dir, "gametest", "BossGameTests.java")
    if not os.path.exists(test):
        err("gametest/BossGameTests.java is missing (regression tests of the boss phases)")
    else:
        tsrc = open(test, encoding="utf-8").read()
        for needle in ("bossTakesDamageInEveryPhase", "getPhase() == 2", "getPhase() == 3", "isLocked"):
            if needle not in tsrc:
                err(f"BossGameTests: expected '{needle}'")
        m = re.search(r'ARENA\s*=\s*"([^"]+)"', tsrc)
        if not m or not os.path.exists(os.path.join(DATA, "structures", m.group(1) + ".nbt")):
            err("BossGameTests: arena template data/donbass/structures/<ARENA>.nbt is missing")
    print("  boss: phase lock / damage rules / game tests checked")


def check_ak_mods():
    """0.3.0: the weapon workbench and the five AK modifications.  Guards against 'fake' bonuses (an effect that is
    documented but not wired into the rifle), against changes of the bullet damage, against a mod resetting the
    loaded ammo, and checks that every piece (item, texture, recipe, lang, loot, registration) exists."""
    mod_dir = os.path.join(JAVA, "com", "donbass", "mod")

    def src(rel):
        path = os.path.join(mod_dir, rel)
        if not os.path.exists(path):
            err(f"{rel} is missing")
            return ""
        return re.sub(r"//[^\n]*|/\*.*?\*/", " ", open(path, encoding="utf-8").read(), flags=re.S)

    mods = src("item/AkMods.java")
    rifle = src("item/AkRifleItem.java")
    client = src("client/AkClientExtensions.java")

    # -- the enum, the items and the constants of the spec
    enum_ids = re.findall(r'\b([A-Z]+)\("([a-z]+)"\)', mods)
    consts = {name: id_ for name, id_ in enum_ids}
    if set(consts) != {"MAGAZINE", "MECHANISM", "STABILIZER", "BARREL", "SPRING"}:
        err(f"AkMods.Mod: expected the five kinds, found {sorted(consts)}")
    spec = {"MAGAZINE_FACTOR": "1.5", "RELOAD_FACTOR": "0.8", "STABILIZER_SPREAD_FACTOR": "0.8",
            "BARREL_SPREAD_FACTOR": "0.9", "SPRING_RATE_FACTOR": "1.1"}
    for name, value in spec.items():
        m = re.search(r"\b" + name + r"\s*=\s*([0-9.]+)D", mods)
        if not m or float(m.group(1)) != float(value):
            err(f"AkMods.{name} must be {value} (the values of the 0.3.0 specification)")
    if re.search(r"rifleDamage|damage", mods, re.I):
        err("AkMods must not touch the bullet damage (the reinforced barrel changes only the spread)")
    if re.search(r"TAG_AMMO|setAmmo|\"Ammo\"", mods):
        err("AkMods must not touch the loaded ammo: installing a mod keeps the rounds in the magazine")
    kits = [i for i in ITEMS if i["kind"] == "akmod"]
    if sorted(i["mod"] for i in kits) != sorted(consts):
        err(f"akmod items {sorted(i['mod'] for i in kits)} do not match AkMods.Mod {sorted(consts)}")

    # -- the rifle must get EVERY number through AkMods (otherwise a mod would be a fake bonus)
    for fn in ("rifleMagazine", "rifleReloadTicks", "rifleSpread", "rifleFireInterval"):
        for name, text in (("AkRifleItem", rifle), ("AkClientExtensions", client)):
            if "DonbassConfig." + fn in text:
                err(f"{name} reads DonbassConfig.{fn}() directly: use AkMods so the modification applies")
    for needle in ("AkMods.magazineSize(stack)", "AkMods.reloadTicks(stack)", "AkMods.spread(stack)",
                   "AkMods.fireInterval(stack)", "AkMods.isShotTick("):
        if needle not in rifle:
            err(f"AkRifleItem does not use {needle}")
    if "AkMods.reloadTicks" not in client:
        err("AkClientExtensions: the reload animation must use AkMods.reloadTicks(stack)")
    if "DonbassConfig.rifleDamage()" not in rifle:
        err("AkRifleItem: the bullet damage must still come from DonbassConfig.rifleDamage()")

    # -- every kit: texture, recipe, lang (item name, effect, GUI names), model
    langs = {c: load(os.path.join(ASSETS, "lang", c + ".json")) or {} for c in ("en_us", "ru_ru", "pl_pl")}
    for kit in kits:
        i, mod_id = kit["id"], consts.get(kit["mod"], "?")
        if not os.path.exists(os.path.join(ASSETS, "textures", "item", i + ".png")):
            err(f"{i}: texture is missing")
        if i not in RECIPES:
            err(f"{i}: no crafting recipe")
        keys = [f"item.donbass.{i}", f"tooltip.donbass.ak_mod_{mod_id}", f"gui.donbass.workbench.mod.{mod_id}",
                f"gui.donbass.workbench.chip.{mod_id}"]
        for code, d in langs.items():
            for k in keys:
                if k not in d:
                    err(f"lang {code}: missing {k}")
    if "weapon_workbench" not in RECIPES:
        err("weapon_workbench: no crafting recipe")
    else:
        ing = json.dumps(RECIPES["weapon_workbench"])
        if "donbass:" not in ing.replace('"result"', "") or "minecraft:" not in ing:
            err("weapon_workbench recipe must combine the mod's industrial items with vanilla ones")
    for tex in ("weapon_workbench_top", "weapon_workbench_side"):
        if not os.path.exists(os.path.join(ASSETS, "textures", "block", tex + ".png")):
            err(f"{tex}: block texture is missing")

    # -- every translation key used by the new Java code exists in every language
    used = set()
    for rel in ("item/AkModItem.java", "item/AkRifleItem.java", "menu/WorkbenchMenu.java",
                "client/WorkbenchScreen.java", "block/WeaponWorkbenchBlockEntity.java"):
        used |= set(re.findall(r'translatable\(\s*"([a-z_.]+)"', src(rel)))
    for code, d in langs.items():
        for k in sorted(used):
            if k not in d:
                err(f"lang {code}: the Java code uses the key {k} which does not exist")

    # -- the workbench: the block is visible, has a block entity that saves, drops its items, opens the menu
    block = src("block/WeaponWorkbenchBlock.java")
    be = src("block/WeaponWorkbenchBlockEntity.java")
    menu = src("menu/WorkbenchMenu.java")
    screen = src("client/WorkbenchScreen.java")
    if not re.search(r"getRenderShape[^{]*\{\s*return\s+RenderShape\.MODEL", block):
        err("WeaponWorkbenchBlock: getRenderShape() must return RenderShape.MODEL (a BaseEntityBlock is invisible otherwise)")
    for needle in ("NetworkHooks.openScreen", "dropContents", "onRemove"):
        if needle not in block:
            err(f"WeaponWorkbenchBlock: expected {needle}")
    for needle in ("saveAdditional", "void load(", "serializeNBT", "deserializeNBT", "getSlotLimit", "isItemValid",
                   "dropContents"):
        if needle not in be:
            err(f"WeaponWorkbenchBlockEntity: expected {needle}")
    for needle in ("clickMenuButton", "quickMoveStack", "stillValid", "AkMods.install", "ContainerData",
                   "bench.setStackInSlot(slot, ItemStack.EMPTY)"):
        if needle not in menu:
            err(f"WorkbenchMenu: expected {needle}")
    if menu.count("AkMods.install") != 1 or "ItemStack.EMPTY" not in menu:
        err("WorkbenchMenu: a kit must be consumed exactly where the mod is installed")
    if "handleInventoryButtonClick" not in screen:
        err("WorkbenchScreen: the Install button must send a menu button click to the server")
    main_src = src("DonbassMod.java")
    for needle in ("ModBlockEntities.BLOCK_ENTITIES.register", "ModMenus.MENUS.register"):
        if needle not in main_src:
            err(f"DonbassMod: {needle} is missing")
    if "MenuScreens.register(ModMenus.WORKBENCH.get()" not in src("client/ClientSetup.java"):
        err("ClientSetup: the workbench screen is not registered")

    # -- loot: the more useful, the rarer (barrel >= spring >= stabilizer >= mechanism >= magazine per chest)
    order = ["barrel", "spring", "stabilizer", "mechanism", "magazine"]
    total = {k: 0 for k in order}
    tables_with_kits = 0
    for p in glob.glob(os.path.join(DATA, "loot_tables", "chests", "*.json")):
        d = load(p) or {"pools": []}
        weights = {k: 0 for k in order}
        for pool in d["pools"]:
            for e in pool["entries"]:
                m = re.fullmatch(r"donbass:ak_mod_([a-z]+)", e.get("name", ""))
                if m and m.group(1) in weights:
                    weights[m.group(1)] += e.get("weight", 1)
        if not any(weights.values()):
            continue
        tables_with_kits += 1
        name = os.path.basename(p)
        for a, b in zip(order, order[1:]):
            if weights[a] < weights[b]:
                err(f"loot {name}: ak_mod_{b} ({weights[b]}) is more common than the less useful ak_mod_{a} ({weights[a]})")
        for k in order:
            total[k] += weights[k]
    if tables_with_kits < 4:
        err(f"the kits appear in only {tables_with_kits} chest tables (factories, blockposts and mines/stations expected)")
    if not total["magazine"] < total["barrel"]:
        err("loot: the extended magazine must be strictly rarer than the barrel")
    for loot_name in ("factory", "blockpost_armory_north", "blockpost_armory_south", "blockpost_supply"):
        if not os.path.exists(os.path.join(DATA, "loot_tables", "chests", loot_name + ".json")):
            err(f"loot table {loot_name} is missing")
    print(f"  ak mods: 5 kinds, workbench, {tables_with_kits} loot tables with kits, effects wired through AkMods")


def check_structure_biomes():
    """0.3.1: the structures of the Donbass dimension must not generate in the ordinary Overworld.  The cause of the
    old bug: the biome tag that every structure points at also listed vanilla biomes (plains, savanna, meadow...)."""
    tag_path = os.path.join(DATA, "tags", "worldgen", "biome", "has_structures.json")
    tag = load(tag_path) or {"values": []}
    own = {"donbass:" + os.path.splitext(os.path.basename(p))[0]
           for p in glob.glob(os.path.join(DATA, "worldgen", "biome", "*.json"))}
    for value in tag["values"]:
        if value not in own:
            err(f"tags/worldgen/biome/has_structures.json lists {value}: structures would generate outside the "
                "Donbass dimension's own biomes (the Overworld structure bug)")
    if not tag["values"]:
        err("tags/worldgen/biome/has_structures.json is empty: the structures could not generate anywhere")
    # the dimension itself must use only those biomes, otherwise the tag would not cover it
    dim = load(os.path.join(DATA, "dimension", "donbass.json")) or {}
    used = {e["biome"] for e in dim.get("generator", {}).get("biome_source", {}).get("biomes", [])}
    if used != set(tag["values"]):
        err(f"dimension biomes {sorted(used)} differ from has_structures {sorted(tag['values'])}")
    count = 0
    for p in glob.glob(os.path.join(DATA, "worldgen", "structure", "*.json")):
        d = load(p) or {}
        count += 1
        biomes = d.get("biomes")
        if biomes != "#donbass:has_structures":
            err(f"structure {os.path.basename(p)}: biomes must be '#donbass:has_structures', is {biomes!r}")
    # no Forge biome modifier may add structures/spawns of the mod to vanilla biomes
    for p in glob.glob(os.path.join(DATA, "forge", "biome_modifier", "*.json")):
        d = load(p) or {}
        if d.get("type") in ("forge:add_spawns",) or "structure" in json.dumps(d):
            err(f"biome modifier {os.path.basename(p)} adds spawns/structures to other biomes")
    print(f"  structure biomes: {count} structures are limited to {sorted(tag['values'])}")


# ======================================================================== 0.4.0 =======================================
def _lang(code):
    return load(os.path.join(ASSETS, "lang", code + ".json")) or {}


def check_names_040():
    """0.4.0: the two uniforms are named after their republic, the boss items after the new boss name, and the old
    names are gone from every displayed text (the registry ids did not change)."""
    langs = {"en": _lang("en_us"), "ru": _lang("ru_ru"), "pl": _lang("pl_pl")}
    marks = {"DPR": {"en": "DPR", "ru": "ДНР", "pl": "DRL"}, "LPR": {"en": "LPR", "ru": "ЛНР", "pl": "ŁRL"}}
    word = {"en": "Military Uniform", "ru": "военной формы", "pl": "munduru wojskowego"}
    seen = set()
    for prefix, rep in (("steppe", "DPR"), ("terricone", "LPR")):
        other = "LPR" if rep == "DPR" else "DPR"
        for piece in ("helmet", "jacket", "trousers", "boots"):
            key = f"item.donbass.{prefix}_{piece}"
            for lg, d in langs.items():
                name = d.get(key, "")
                if marks[rep][lg] not in name:
                    err(f"uniform {key} ({lg}): '{name}' does not name {marks[rep][lg]}")
                if marks[other][lg] in name:
                    err(f"uniform {key} ({lg}): '{name}' names the other republic")
                if word[lg] not in name:
                    err(f"uniform {key} ({lg}): '{name}' lacks the wording '{word[lg]}'")
                if (lg, name) in seen:
                    err(f"uniform {key} ({lg}): the name '{name}' is used twice")
                seen.add((lg, name))
    # the name «Председатель Угольного края» / "Chairman of the Coal Region" / "Przewodniczący Kraju Węglowego" is
    # declined in ru / pl ("Председателя", "Przewodniczącego"), so the stem of the title and the fixed words are checked
    for k, v in langs["en"].items():
        if "DNR" in v or "LNR" in v:
            err(f"lang en: {k} uses DNR / LNR: the English texts say DPR / LPR ('{v}')")
    boss = {"en": ("Chairman", "Coal Region"), "ru": ("Председател", "Угольного края"),
            "pl": ("Przewodnicząc", "Kraju Węglowego")}
    nominative = {"en": "Chairman of the Coal Region", "ru": "Председатель Угольного края",
                  "pl": "Przewodniczący Kraju Węglowego"}
    for lg, d in langs.items():
        if d.get("entity.donbass.combine_director") != nominative[lg]:
            err(f"boss name: entity.donbass.combine_director ({lg}) must be exactly '{nominative[lg]}'")
    # entity, the three items, the messages and the siren tooltip must carry the new name
    for key in ("entity.donbass.combine_director", "item.donbass.combine_siren", "item.donbass.director_pickaxe",
                "item.donbass.director_badge", "message.donbass.director_summon", "message.donbass.director_defeated",
                "message.donbass.siren_busy", "message.donbass.siren_no_room", "tooltip.donbass.siren"):
        for lg, d in langs.items():
            if not all(part in d.get(key, "") for part in boss[lg]):
                err(f"boss name: {key} ({lg}) = '{d.get(key)}' does not contain the new boss name {boss[lg]}")
    old = ("Терриконов", "Terrikonov", "Terrikonow", "Директорск", "Именная кирка директора", "dyrektora", "Director's",
           "Combine Siren", "Сирена комбината", "Syrena kombinatu", "Steppe Field", "Steppe Combat", "Terricone Field",
           "Terricone Combat", "«Степь»", "«Терикон»", "„Step”", "„Hałda”")
    for lg, d in langs.items():
        for k, v in d.items():
            for o in old:
                # "Syrena kombinatu wyje" is the subtitle of the siren SOUND (a factory siren), not an item name
                if o in v and k != "subtitles.donbass.item.director_siren":
                    err(f"lang {lg}: {k} still contains the old name '{o}'")
    # registry ids are the same as before (old worlds keep their items)
    ids = {i["id"] for i in ITEMS}
    for needed in ("combine_siren", "director_pickaxe", "director_badge", "steppe_helmet", "steppe_jacket",
                   "steppe_trousers", "steppe_boots", "terricone_helmet", "terricone_jacket", "terricone_trousers",
                   "terricone_boots"):
        if needed not in ids:
            err(f"registry id {needed} is gone: existing worlds would lose the item")
    if "combine_director" not in registered_entities():
        err("entity id combine_director is gone")
    print("  names: 8 uniform pieces (DPR / LPR), boss name in 9 texts x 3 languages, no old names left")


# the 0.3.1 values of everything that must not change, and the 0.4.0 values of what was rebalanced
STRUCTURE_SETS_040 = {
    # name: (salt, spacing, separation, exclusion zone)
    "shallow_mines": (1730102, 10, 4, None),
    "active_mines": (1730103, 20, 7, ("miners_settlements", 3)),
    "deep_mines": (1730104, 24, 8, ("miners_settlements", 3)),
}


def _structure_set(name):
    d = load(os.path.join(DATA, "worldgen", "structure_set", name + ".json")) or {}
    pl = d.get("placement", {})
    ez = pl.get("exclusion_zone")
    return pl, (ez["other_set"].replace("donbass:", ""), ez["chunk_count"]) if ez else None, d


def check_structure_rebalance():
    """0.4.0: settlements a little rarer (larger spacing), checkpoints a little more frequent (smaller spacing), the
    mines exactly as before.  random_spread puts ONE candidate into every spacing x spacing region of chunks, so the
    density is 1 / spacing^2; the separation only keeps neighbouring candidates apart.  Moderate = within 25 %."""
    for name, (salt, spacing, sep, ez) in STRUCTURE_SETS_040.items():
        pl, zone, _ = _structure_set(name)
        got = (pl.get("salt"), pl.get("spacing"), pl.get("separation"), zone)
        if pl.get("type") != "minecraft:random_spread" or got != (salt, spacing, sep, ez):
            err(f"structure set {name} changed: {got} != {(salt, spacing, sep, ez)} (the mines must not change)")
    for name in ("shallow_mines", "active_mines", "deep_mines"):
        _, _, d = _structure_set(name)
        if len(d.get("structures", [])) != 1:
            err(f"structure set {name}: the structure list changed")
    s_pl, _, _ = _structure_set("miners_settlements")
    b_pl, b_zone, _ = _structure_set("blockposts")
    if s_pl.get("salt") != 1730101 or b_pl.get("salt") != 1730107:
        err("the salts of settlements / blockposts changed (the layout of existing candidates would shuffle)")
    if not s_pl.get("spacing", 0) > 16:
        err(f"settlements must be rarer than in 0.3.1 (spacing > 16), spacing is {s_pl.get('spacing')}")
    if not b_pl.get("spacing", 99) < 14:
        err(f"checkpoints must be more frequent than in 0.3.1 (spacing < 14), spacing is {b_pl.get('spacing')}")
    s_ratio = 16 ** 2 / s_pl.get("spacing", 16) ** 2
    b_ratio = 14 ** 2 / b_pl.get("spacing", 14) ** 2
    if not 0.75 <= s_ratio < 1.0:
        err(f"settlement density x{s_ratio:.2f} of the old one: not 'a little rarer' (0.75 .. 1.0)")
    if not 1.0 < b_ratio <= 1.25:
        err(f"checkpoint density x{b_ratio:.2f} of the old one: not 'a little more frequent' (1.0 .. 1.25)")
    for pl in (s_pl, b_pl):
        if not 0 < pl.get("separation", 0) < pl.get("spacing", 0):
            err(f"structure set: separation must be positive and smaller than the spacing: {pl}")
    if s_pl.get("separation") != 6 or b_pl.get("separation") != 5 or b_zone != ("miners_settlements", 3):
        err("separation / exclusion zone of the settlements or checkpoints changed (not part of the rebalance)")
    print(f"  structure rebalance: settlements spacing {s_pl['spacing']} (density x{s_ratio:.2f}), checkpoints spacing "
          f"{b_pl['spacing']} (x{b_ratio:.2f}), 3 mine sets unchanged")


def _template_blocks(rel):
    t = read_template(os.path.join(DATA, "structures", rel))
    names = [e["Name"] for e in t["palette"]]
    return {tuple(b["pos"]): names[b["state"]] for b in t["blocks"]}, tuple(t["size"])


FLAGS_040 = {
    # template -> (faction label, stripes top to bottom)
    "military/blockpost_north.nbt": ("DPR", ["minecraft:black_wool", "minecraft:blue_wool", "minecraft:red_wool"]),
    "military/blockpost_south.nbt": ("LPR", ["minecraft:light_blue_wool", "minecraft:blue_wool", "minecraft:red_wool"]),
}


def check_flags():
    """0.4.0: every checkpoint template carries exactly one flag, of the republic whose squad holds it: the DPR flag
    (black / blue / red) on the "north" (DPR) post, the LPR flag (light blue / blue / red) on the "south" (LPR) post.
    The flag is part of the template (generated with the structure), hangs on a pole that stands on the ground layer,
    towers above the walls and the watchtower, and is not inside anything."""
    from structures_military import SQUADS
    if set(SQUADS) != {"north", "south"}:
        err("structures_military.SQUADS changed")
    for rel, (label, stripes) in FLAGS_040.items():
        blocks, (sx, sy, sz) = _template_blocks(rel)
        wool = {pos: n for pos, n in blocks.items() if n.endswith("_wool")}
        if len(wool) != 12:
            err(f"{rel}: expected one flag of 4 x 3 wool blocks, found {len(wool)} wool blocks")
            continue
        xs = sorted({x for x, _, _ in wool}), sorted({y for _, y, _ in wool}), sorted({z for _, _, z in wool})
        if len(xs[2]) != 1 or xs[0] != list(range(xs[0][0], xs[0][0] + 4)) or xs[1] != list(range(xs[1][0], xs[1][0] + 3)):
            err(f"{rel}: the wool is not one flat 4 x 3 rectangle ({xs})")
            continue
        z, x0, y_top = xs[2][0], xs[0][0], xs[1][-1]
        for row, stripe in enumerate(stripes):                       # stripes from the top down
            for x in xs[0]:
                got = wool.get((x, y_top - row, z))
                if got != stripe:
                    err(f"{rel}: {label} flag stripe {row + 1} at x={x}: {got} != {stripe}")
        # the other republic's top colour must not appear anywhere in this template
        for other_rel, (other_label, other_stripes) in FLAGS_040.items():
            if other_rel != rel and other_stripes[0] in wool.values():
                err(f"{rel}: contains the {other_label} flag colour {other_stripes[0]}")
        # the pole: a continuous girder column right next to the flag, standing on a solid ground-layer block
        pole = [pos for pos, n in blocks.items() if n == "donbass:steel_girder" and pos[0] == x0 - 1 and pos[2] == z]
        ys = sorted(y for _, y, _ in pole)
        if not ys or ys != list(range(ys[0], ys[-1] + 1)):
            err(f"{rel}: the flag pole is missing or has gaps")
            continue
        if ys[-1] < y_top:
            err(f"{rel}: the pole (top y={ys[-1]}) is lower than the flag (top y={y_top})")
        base = blocks.get((x0 - 1, ys[0] - 1, z))
        if base is None or base == "minecraft:air" or base.endswith("_wool"):
            err(f"{rel}: the pole does not stand on solid ground ({base} below y={ys[0]})")
        if ys[0] != 2:
            err(f"{rel}: the pole must start on the yard layer (y=2), starts at y={ys[0]}")
        # nothing floats: every flag block touches the pole or the next flag block towards the pole
        for (x, y, zz) in wool:
            nb = (x - 1, y, zz)
            if nb not in wool and nb not in {(x0 - 1, py, z) for py in ys}:
                err(f"{rel}: flag block {(x, y, zz)} is not attached")
        # visible from afar: above the walls (y <= 3) and above the watchtower (its highest block)
        tower_top = max(y for (x, y, zz), n in blocks.items() if n == "donbass:slag_bricks" and x >= 12 and zz >= 12)
        wall_top = 3
        if min(y for _, y, _ in wool) <= wall_top or y_top <= tower_top:
            err(f"{rel}: the flag (y {min(y for _, y, _ in wool)}..{y_top}) must be above the walls (y {wall_top}) and "
                f"the tower (top y={tower_top})")
        # not inside walls and not hanging into other blocks: the cells around the flag are free of solid blocks
        for (x, y, zz) in wool:
            for dx, dy, dz in ((1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
                n = blocks.get((x + dx, y + dy, zz + dz))
                if n is not None and n != "minecraft:air" and not n.endswith("_wool"):
                    err(f"{rel}: flag block {(x, y, zz)} touches {n} at {(x + dx, y + dy, zz + dz)}")
        if x0 + 3 >= sx or y_top >= sy:
            err(f"{rel}: the flag leaves the template box")
    # no other structure carries a faction flag: wool in templates other than the checkpoints and the (white) pennants
    for path in glob.glob(os.path.join(DATA, "structures", "**", "*.nbt"), recursive=True):
        rel = os.path.relpath(path, os.path.join(DATA, "structures")).replace(os.sep, "/")
        if rel in FLAGS_040:
            continue
        blocks, _ = _template_blocks(rel)
        for n in blocks.values():
            if n in ("minecraft:black_wool", "minecraft:light_blue_wool"):
                err(f"{rel}: has {n}: a republic's flag only belongs to the checkpoints")
    print("  flags: DPR (black/blue/red) on blockpost_north, LPR (light blue/blue/red) on blockpost_south, one each")


def _lang_keys_in_java(rel_dir):
    keys = set()
    for p in glob.glob(os.path.join(JAVA, "com", "donbass", "mod", rel_dir, "**", "*.java"), recursive=True):
        keys |= set(re.findall(r'"(command\.donbass\.[a-z_.0-9]+)"', open(p, encoding="utf-8").read()))
    return {k for k in keys if not k.endswith(".")}      # "command.donbass.help." + id is a prefix, not a key


def check_commands_and_boss_health():
    """0.4.0: /donbass bosshp and /donbasshelp.  Static: wiring, permissions, the single place where the multiplier is
    applied, the persistence, the help text in three languages.  The parsing itself is run by tools/run_selfchecks.sh."""
    cmd = java_text("command/DonbassCommands.java")
    mult = java_text("boss/BossMultiplier.java")
    sett = java_text("boss/BossSettings.java")
    boss = java_text("entity/CombineDirectorEntity.java")
    # --- commands
    if "@Mod.EventBusSubscriber" not in cmd or "Bus.FORGE" not in cmd or "RegisterCommandsEvent" not in cmd:
        err("DonbassCommands must subscribe to RegisterCommandsEvent on the FORGE bus")
    for lit in ('Commands.literal("donbasshelp")', 'Commands.literal("donbass")', 'Commands.literal("bosshp")',
                'Commands.argument("multiplier", StringArgumentType.greedyString())'):
        if lit not in cmd:
            err(f"DonbassCommands: {lit} is missing")
    body = method_body(cmd, r"private static int setBossHealth\([^)]*\)[^{]*\{")
    if body is None:
        err("DonbassCommands.setBossHealth not found")
    else:
        if "hasPermission(OP_LEVEL)" not in body or body.index("hasPermission") > body.index("BossMultiplier.parse"):
            err("setBossHealth must check the operator permission BEFORE it parses or stores anything")
        if "BossSettings.get" not in body or "setHealthMultiplier(" not in body:
            err("setBossHealth does not store the multiplier in BossSettings")
    show = method_body(cmd, r"private static int showBossHealth\([^)]*\)[^{]*\{")
    if show is None or "hasPermission" in show or "setHealthMultiplier" in show:
        err("showBossHealth (no argument) must be open to everybody and must not change anything")
    m = re.search(r"OP_LEVEL\s*=\s*(\d+)", cmd)
    if not m or int(m.group(1)) < 2:
        err("OP_LEVEL must be at least 2 (operator)")
    help_body = method_body(cmd, r"private static int help\([^)]*\)[^{]*\{")
    if help_body is None or "hasPermission" in help_body:
        err("/donbasshelp must be open to everybody (no permission check)")
    # --- the multiplier: limits, parsing, one single application
    lim = {k: float(v) for k, v in re.findall(r"public static final double (DEFAULT|MIN|MAX|ATTRIBUTE_MAX_HEALTH)\s*=\s*([0-9.]+)D", mult)}
    if lim.get("DEFAULT") != 1.0 or not 0 < lim.get("MIN", 0) < 1.0 <= lim.get("MAX", 0):
        err(f"BossMultiplier limits are wrong: {lim}")
    if lim.get("MAX", 0) * 320.0 > lim.get("ATTRIBUTE_MAX_HEALTH", 0) + 1e-6:
        err("BossMultiplier.MAX x the default boss health (320) is above the max_health attribute limit")
    if "parseDouble" in mult and "NUMBER.matcher" not in mult:
        err("BossMultiplier parses without validating the text first (Java accepts '1e3', 'NaN', '1f'...)")
    # the multiplier is applied in setUp() and nowhere else of the boss
    uses = [mm.start() for mm in re.finditer(r"BossMultiplier\.health\(|BossSettings\.get\(", boss)]
    setup = method_body(boss, r"private void setUp\(\)\s*\{")
    if setup is None or not uses:
        err("CombineDirectorEntity.setUp does not read the multiplier")
    else:
        a = boss.index(setup)
        if any(not (a <= u < a + len(setup)) for u in uses):
            err("the boss multiplier is used outside setUp(): it could be applied again")
        if setup.index("if (initialized)") > setup.index("BossSettings.get"):
            err("setUp(): the 'initialized' guard must come before the multiplier is read")
        if "MAX_HEALTH" not in setup or setup.count("MAX_HEALTH") != 1:
            err("setUp() must set MAX_HEALTH exactly once")
    if boss.count("Attributes.MAX_HEALTH") != 2:      # createAttributes() default + setUp()
        err("MAX_HEALTH is set somewhere else in the boss: the multiplier could be bypassed or applied twice")
    for fn in ("applyPhaseStats", "updatePhase", "enterPhase"):
        b = method_body(boss, r"(private|protected|public) \w+ " + fn + r"\([^)]*\)\s*\{")
        if b is None or "BossMultiplier" in b or "BossSettings" in b or "MAX_HEALTH" in b:
            err(f"{fn}() must not touch the health multiplier / max health (phases work on health / max health)")
    if "getHealth() / this.getMaxHealth()" not in boss:
        err("the phases must be computed from health / max health")
    if "ATTACK_DAMAGE" in setup or "bossDamageMultiplier" in (setup or ""):
        err("setUp() must not touch the damage")
    # --- persistence
    if "extends SavedData" not in sett or "setDirty()" not in sett or "getDataStorage().computeIfAbsent" not in sett:
        err("BossSettings must be a SavedData in the overworld's data storage and call setDirty() on change")
    if "public CompoundTag save(CompoundTag" not in sett or "putDouble" not in sett:
        err("BossSettings does not write the multiplier")
    if "server.overworld()" not in sett:
        err("BossSettings must live in the overworld's data storage (one value for the whole world)")
    # --- texts
    langs = {"en": _lang("en_us"), "ru": _lang("ru_ru"), "pl": _lang("pl_pl")}
    sections = [(i, int(a), int(b)) for i, a, b in re.findall(r'new Section\("(\w+)",\s*(\d+),\s*(\d+)\)', cmd)]
    if [s[0] for s in sections] != ["factions", "weapons", "world", "boss", "bosshp", "coop"]:
        err(f"/donbasshelp sections changed: {[s[0] for s in sections]}")
    needed = {"command.donbass.help.title", "command.donbass.help.footer", "command.donbass.usage"}
    for sid, lines, examples in sections:
        needed.add(f"command.donbass.help.{sid}.title")
        needed |= {f"command.donbass.help.{sid}.{i}" for i in range(1, lines + 1)}
        needed |= {f"command.donbass.help.{sid}.ex{i}" for i in range(1, examples + 1)}
    for e in re.findall(r'\("(command\.donbass\.bosshp\.error\.[a-z_]+)"\)', mult):
        needed.add(e)
    needed |= {"command.donbass.bosshp.current", "command.donbass.bosshp.usage", "command.donbass.bosshp.set",
               "command.donbass.bosshp.no_permission"}
    needed |= _lang_keys_in_java("command")
    for lg, d in langs.items():
        for k in sorted(needed):
            if k not in d:
                err(f"lang {lg}: missing {k}")
        extra = {k for k in d if k.startswith("command.donbass.") and k not in needed}
        if extra:
            err(f"lang {lg}: unused command texts {sorted(extra)[:4]}")
        for k, v in d.items():
            if k.startswith("command.donbass.") and re.search(r"%(?!%|\d\$s|s)", v.replace("%%", "")):
                err(f"lang {lg}: {k} has a lone '%' (write '%%'): {v}")
    # the shown limits and the co-op table (the values of the task) agree with the code and fit into the limits
    lo, hi = lim.get("MIN", 0), lim.get("MAX", 0)
    for lg, d in langs.items():
        t = d.get("command.donbass.help.bosshp.3", "")
        if f"{lo:g}" not in t or f"{hi:g}" not in t or "1024" not in t:
            err(f"lang {lg}: bosshp help does not state the limits {lo:g}..{hi:g} and 1024")
        rows = [d.get(f"command.donbass.help.coop.{i}", "") for i in range(1, 6)]
        for row, want in zip(rows, ("1.0", "1.5", "2.0", "2.5", "3.0")):
            if f"×{want}" not in row and f"x{want}" not in row:
                err(f"lang {lg}: co-op row '{row}' should end with x{want}")
            if not lo <= float(want) <= hi:
                err(f"co-op multiplier {want} is outside the allowed range")
        for i, want in ((1, "1"), (2, "2"), (3, "3"), (4, "4"), (5, "5")):
            if not rows[i - 1].startswith(want):
                err(f"lang {lg}: co-op row {i} '{rows[i - 1]}' must start with {want}")
        if "×" not in d.get("command.donbass.help.coop.5", "") and "x" not in d.get("command.donbass.help.coop.5", ""):
            err(f"lang {lg}: co-op table is incomplete")
        if not d.get("command.donbass.help.coop.6"):
            err(f"lang {lg}: the co-op note ('approximate values') is missing")
        # the help describes only what exists: crude guard against announcing planned things
        for k, v in d.items():
            if k.startswith("command.donbass.help.") and re.search(r"\b(planned|coming soon|TODO|скоро|планируется|wkrótce)\b", v, re.I):
                err(f"lang {lg}: {k} mentions something only planned")
    print(f"  commands: /donbasshelp ({len(sections)} blocks) and /donbass bosshp [{lo:g}..{hi:g}], "
          f"{len(needed)} texts x 3 languages, multiplier applied only in setUp(), persisted in SavedData")


def _loot_sources():
    """item id -> set of ('chest'|'entity'|'block', table) for every loot table of the mod."""
    out = {}
    for p in glob.glob(os.path.join(DATA, "loot_tables", "**", "*.json"), recursive=True):
        rel = os.path.relpath(p, os.path.join(DATA, "loot_tables")).replace(os.sep, "/")[:-5]
        kind, _, name = rel.partition("/")
        txt = open(p, encoding="utf-8").read()
        for m in re.finditer(r'"name":\s*"(donbass:[a-z_]+|minecraft:[a-z_]+)"', txt):
            item = m.group(1)
            if kind == "blocks" and item == "donbass:" + name:
                continue                                    # a block that only drops itself is not a source
            out.setdefault(item, set()).add((kind, name))
    return out


BOSS_ONLY_TABLES = {("entity", "combine_director")}


def check_siren_recipe():
    """0.4.0: the item that calls the boss has an expensive recipe made of things the player gets in the Donbass before
    the first fight (never the boss's own badge / pickaxe / siren)."""
    r = RECIPES.get("combine_siren")
    if not r or r["type"] != "minecraft:crafting_shaped" or r["result"]["item"] != "donbass:combine_siren":
        err("RECIPES['combine_siren'] is missing or does not make the siren")
        return
    grid = "".join(r["pattern"])
    slots = [r["key"][c]["item"] for c in grid if c != " "]
    ours = [i for i in slots if i.startswith("donbass:")]
    if len(slots) < 8:
        err(f"siren recipe uses only {len(slots)} slots: it must be expensive (8-9 filled slots)")
    if len(ours) * 3 < len(slots) * 2:
        err(f"siren recipe: only {len(ours)} of {len(slots)} slots are Donbass items (must be mostly Donbass items)")
    if len(set(ours)) < 4:
        err("siren recipe: at least four different Donbass items are required")
    if len(set(slots) - set(ours)) > 3:
        err("siren recipe: at most three kinds of vanilla ingredients")
    for banned in ("donbass:director_badge", "donbass:director_pickaxe", "donbass:combine_siren",
                   "donbass:coal_chestplate"):
        if banned in slots and banned != "donbass:coal_chestplate":
            err(f"siren recipe uses {banned}, which only the boss / the siren itself gives")
    sources = _loot_sources()
    recipe_by_result = {}
    for name, rec in RECIPES.items():
        res = rec["result"]["item"] if isinstance(rec["result"], dict) else rec["result"]
        recipe_by_result.setdefault(res, []).append((name, rec))

    def ingredients(rec):
        if "ingredients" in rec:
            return [i.get("item") for i in rec["ingredients"] if "item" in i]
        if "key" in rec:
            return [v["item"] for v in rec["key"].values() if "item" in v]
        return [rec["ingredient"]["item"]] if "ingredient" in rec else []

    def obtainable(item, trail=()):
        """True if the item can be found or made without the boss; returns the loot-only leaves used."""
        if item.startswith("minecraft:"):
            return item_exists(item)
        if item in trail:
            return False
        for kind, name in sources.get(item, ()):
            if (kind, name) not in BOSS_ONLY_TABLES:
                return True
        for _, rec in recipe_by_result.get(item, []):
            if all(obtainable(i, trail + (item,)) for i in ingredients(rec) if i):
                return True
        return False

    for item in sorted(set(slots)):
        if not obtainable(item):
            err(f"siren recipe: {item} cannot be obtained without the boss (no chest/drop/block source and no recipe)")
    # at least one root of the tree that is pure loot (rusty gear / iron scrap): the recipe needs exploration
    loot_roots = {"donbass:rusty_gear", "donbass:iron_scrap"}

    def roots(item, trail=()):
        found = set()
        if item.startswith("minecraft:") or item in trail:
            return found
        if item in loot_roots:
            found.add(item)
        for _, rec in recipe_by_result.get(item, []):
            for i in ingredients(rec):
                found |= roots(i, trail + (item,))
        return found

    leaves = set()
    for item in slots:
        leaves |= roots(item)
    if not leaves:
        err("siren recipe: the tree contains no loot-only item (rusty gear / iron scrap), so no exploration is needed")
    # the sources of the plain Donbass slots (so the report can say where each comes from)
    where = {}
    for item in sorted(set(ours)):
        srcs = sorted({f"{k}:{n}" for k, n in sources.get(item, ()) if (k, n) not in BOSS_ONLY_TABLES})
        made = [n for n, _ in recipe_by_result.get(item, [])]
        where[item] = (len(srcs), len(made))
    print(f"  siren recipe: {len(slots)} slots, {len(ours)} Donbass items ({len(set(ours))} kinds), all obtainable without "
          f"the boss, loot-only roots: {sorted(x.split(':')[1] for x in leaves)}")


def main():
    print("Validating Donbass mod...")
    for fn in (check_templates, check_sounds_and_gear, check_assets, check_lang, check_recipes_and_loot,
               check_rifle_model, check_worldgen, check_java, check_java_imports, check_boss, check_ak_mods, check_structure_biomes,
               check_names_040, check_structure_rebalance, check_flags, check_commands_and_boss_health,
               check_siren_recipe):
        fn()
    for w in warnings:
        print("  warning:", w)
    for e in errors:
        print("  ERROR:", e)
    print(f"\n{len(errors)} error(s), {len(warnings)} warning(s)")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()

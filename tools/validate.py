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


def main():
    print("Validating Donbass mod...")
    for fn in (check_templates, check_sounds_and_gear, check_assets, check_lang, check_recipes_and_loot,
               check_rifle_model, check_worldgen, check_java, check_java_imports, check_boss, check_ak_mods, check_structure_biomes):
        fn()
    for w in warnings:
        print("  warning:", w)
    for e in errors:
        print("  ERROR:", e)
    print(f"\n{len(errors)} error(s), {len(warnings)} warning(s)")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()

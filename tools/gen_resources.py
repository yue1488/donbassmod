"""Generates blockstates, models, loot tables, recipes, tags, lang files and the
Java registries (ModBlocks / ModItems) from content.py.  Run from anywhere."""
import json
import os
import shutil

import rifle_model
from content import BLOCKS, ITEMS, LANG_EXTRA, RECIPES, MOD_ID

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.normpath(os.path.join(HERE, ".."))
RES = os.path.join(PROJ, "src", "main", "resources")
ASSETS = os.path.join(RES, "assets", MOD_ID)
DATA = os.path.join(RES, "data", MOD_ID)
JAVA = os.path.join(PROJ, "src", "main", "java", "com", "donbass", "mod", "registry")
BY_ID = {b["id"]: b for b in BLOCKS}
N = MOD_ID + ":"


def wj(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


def tex_of(b):
    """Resolve the texture(s) of a block (slabs/stairs use their base block)."""
    return BY_ID[b["base"]]["tex"] if b["base"] else b["tex"]


# ------------------------------------------------- blockstates & models ----
def gen_block_assets():
    for b in BLOCKS:
        i, k = b["id"], b["kind"]
        bs = os.path.join(ASSETS, "blockstates", i + ".json")
        mdl = lambda name: os.path.join(ASSETS, "models", "block", name + ".json")
        item_model = os.path.join(ASSETS, "models", "item", i + ".json")
        t = tex_of(b)

        if k in ("cube", "falling", "magma", "glass"):
            wj(bs, {"variants": {"": {"model": N + "block/" + i}}})
            m = {"parent": "minecraft:block/cube_all", "textures": {"all": N + "block/" + t}}
            if k == "glass":
                m["render_type"] = "minecraft:translucent"
            wj(mdl(i), m)
            wj(item_model, {"parent": N + "block/" + i})

        elif k == "pillar":
            side, end = t
            wj(bs, {"variants": {
                "axis=y": {"model": N + "block/" + i},
                "axis=z": {"model": N + "block/" + i + "_horizontal", "x": 90},
                "axis=x": {"model": N + "block/" + i + "_horizontal", "x": 90, "y": 90}}})
            tx = {"end": N + "block/" + end, "side": N + "block/" + side}
            wj(mdl(i), {"parent": "minecraft:block/cube_column", "textures": tx})
            wj(mdl(i + "_horizontal"), {"parent": "minecraft:block/cube_column_horizontal", "textures": tx})
            wj(item_model, {"parent": N + "block/" + i})

        elif k == "slab":
            base = b["base"]
            wj(bs, {"variants": {
                "type=bottom": {"model": N + "block/" + i},
                "type=top": {"model": N + "block/" + i + "_top"},
                "type=double": {"model": N + "block/" + base}}})
            tx = {"bottom": N + "block/" + t, "top": N + "block/" + t, "side": N + "block/" + t}
            wj(mdl(i), {"parent": "minecraft:block/slab", "textures": tx})
            wj(mdl(i + "_top"), {"parent": "minecraft:block/slab_top", "textures": tx})
            wj(item_model, {"parent": N + "block/" + i})

        elif k == "stairs":
            variants = {}
            rots = {"east": 0, "south": 90, "west": 180, "north": 270}
            for facing, rot in rots.items():
                for half in ("bottom", "top"):
                    for shape in ("straight", "inner_left", "inner_right", "outer_left", "outer_right"):
                        model = {"straight": "", "inner_left": "_inner", "inner_right": "_inner",
                                 "outer_left": "_outer", "outer_right": "_outer"}[shape]
                        left = shape.endswith("left")
                        if half == "bottom":
                            y = (rot - 90) % 360 if left else rot
                            entry = {"model": N + "block/" + i + model}
                        else:
                            y = rot if left else (rot + 90) % 360
                            if shape == "straight":
                                y = rot
                            entry = {"model": N + "block/" + i + model, "x": 180}
                        if y:
                            entry["y"] = y
                        if entry.get("x") or entry.get("y"):
                            entry["uvlock"] = True
                        variants[f"facing={facing},half={half},shape={shape}"] = entry
            wj(bs, {"variants": variants})
            tx = {"bottom": N + "block/" + t, "top": N + "block/" + t, "side": N + "block/" + t}
            wj(mdl(i), {"parent": "minecraft:block/stairs", "textures": tx})
            wj(mdl(i + "_inner"), {"parent": "minecraft:block/inner_stairs", "textures": tx})
            wj(mdl(i + "_outer"), {"parent": "minecraft:block/outer_stairs", "textures": tx})
            wj(item_model, {"parent": N + "block/" + i})

        elif k == "pane":
            m = lambda n: N + "block/" + i + "_" + n
            wj(bs, {"multipart": [
                {"apply": {"model": m("post")}},
                {"when": {"north": "true"}, "apply": {"model": m("side")}},
                {"when": {"east": "true"}, "apply": {"model": m("side"), "y": 90}},
                {"when": {"south": "true"}, "apply": {"model": m("side_alt")}},
                {"when": {"west": "true"}, "apply": {"model": m("side_alt"), "y": 90}},
                {"when": {"north": "false"}, "apply": {"model": m("noside")}},
                {"when": {"east": "false"}, "apply": {"model": m("noside_alt")}},
                {"when": {"south": "false"}, "apply": {"model": m("noside_alt"), "y": 90}},
                {"when": {"west": "false"}, "apply": {"model": m("noside"), "y": 270}}]})
            tx = {"pane": N + "block/" + t, "edge": N + "block/" + t}
            for part in ("post", "side", "side_alt", "noside", "noside_alt"):
                wj(mdl(i + "_" + part), {"parent": "minecraft:block/template_glass_pane_" + part,
                                         "render_type": "minecraft:cutout", "textures": tx})
            wj(item_model, {"parent": "minecraft:item/generated", "textures": {"layer0": N + "block/" + t}})
        else:
            raise ValueError("unknown kind " + k)


def gen_item_assets():
    for it in ITEMS:
        path = os.path.join(ASSETS, "models", "item", it["id"] + ".json")
        k = it["kind"]
        if k == "egg":
            wj(path, {"parent": "minecraft:item/template_spawn_egg"})
        elif k == "rifle":
            # a real 3D model (the flat sprite lay on its side in the hands): tools/rifle_model.py
            wj(path, rifle_model.model_json(N + "item/" + it["id"] + "_model", N + "item/" + it["id"]))
        else:
            parent = "minecraft:item/handheld" if k == "pickaxe" else "minecraft:item/generated"
            wj(path, {"parent": parent, "textures": {"layer0": N + "item/" + it["id"]}})


# ----------------------------------------------------------- loot tables ----
SILK = {"condition": "minecraft:match_tool",
        "predicate": {"enchantments": [{"enchantment": "minecraft:silk_touch", "levels": {"min": 1}}]}}
SURVIVES = {"condition": "minecraft:survives_explosion"}


def item_name(x):
    return x if ":" in x else N + x


def gen_loot():
    for b in BLOCKS:
        i = b["id"]
        loot = b["loot"]
        if b["kind"] == "glass":
            pool = {"rolls": 1.0, "bonus_rolls": 0.0,
                    "entries": [{"type": "minecraft:item", "name": N + i}], "conditions": [SILK]}
        elif b["kind"] == "slab":
            pool = {"rolls": 1.0, "bonus_rolls": 0.0, "entries": [{
                "type": "minecraft:item", "name": N + i,
                "functions": [
                    {"function": "minecraft:set_count", "count": 2.0, "add": False,
                     "conditions": [{"condition": "minecraft:block_state_property", "block": N + i,
                                     "properties": {"type": "double"}}]},
                    {"function": "minecraft:explosion_decay"}]}]}
        elif loot == "self":
            pool = {"rolls": 1.0, "bonus_rolls": 0.0,
                    "entries": [{"type": "minecraft:item", "name": N + i}], "conditions": [SURVIVES]}
        else:
            _, drop, lo, hi, fortune = loot
            funcs = [{"function": "minecraft:set_count",
                      "count": {"type": "minecraft:uniform", "min": float(lo), "max": float(hi)},
                      "add": False}]
            if fortune:
                funcs.append({"function": "minecraft:apply_bonus", "enchantment": "minecraft:fortune",
                              "formula": "minecraft:ore_drops"})
            funcs.append({"function": "minecraft:explosion_decay"})
            pool = {"rolls": 1.0, "bonus_rolls": 0.0, "entries": [{
                "type": "minecraft:alternatives", "children": [
                    {"type": "minecraft:item", "name": N + i, "conditions": [SILK]},
                    {"type": "minecraft:item", "name": item_name(drop), "functions": funcs}]}]}
        wj(os.path.join(DATA, "loot_tables", "blocks", i + ".json"),
           {"type": "minecraft:block", "pools": [pool], "random_sequence": N + "blocks/" + i})


# --------------------------------------------------------------- recipes ----
def recipe_category(r):
    """Recipe-book tab: building/equipment/misc for crafting, blocks/misc for cooking."""
    result = r["result"]["item"] if isinstance(r["result"], dict) else r["result"]
    own = result[len(N):] if result.startswith(N) else None
    if r["type"] in ("minecraft:smelting", "minecraft:blasting"):
        return "blocks" if own in BY_ID else "misc"
    if own in BY_ID:
        return "building"
    equipment = {"miners_pickaxe", "ak_rifle"} | {i["id"] for i in ITEMS if i["kind"] == "armor"}
    return "equipment" if own in equipment else "misc"


def gen_recipes():
    for name, r in RECIPES.items():
        out = {"type": r["type"], "category": recipe_category(r)}
        out.update({k: v for k, v in r.items() if k != "type"})
        wj(os.path.join(DATA, "recipes", name + ".json"), out)


# ------------------------------------------------------------------ tags ----
def gen_tags():
    def tag(path, values):
        wj(path, {"replace": False, "values": sorted(values)})

    for tool in ("pickaxe", "shovel", "axe"):
        vals = [N + b["id"] for b in BLOCKS if b["tool"] == tool]
        if vals:
            tag(os.path.join(RES, "data", "minecraft", "tags", "blocks", "mineable", tool + ".json"), vals)
    stone = [N + b["id"] for b in BLOCKS if b["tier"] == "stone"]
    tag(os.path.join(RES, "data", "minecraft", "tags", "blocks", "needs_stone_tool.json"), stone)

    slabs = [N + b["id"] for b in BLOCKS if b["kind"] == "slab"]
    stairs = [N + b["id"] for b in BLOCKS if b["kind"] == "stairs"]
    for kind_dir in ("blocks", "items"):
        tag(os.path.join(RES, "data", "minecraft", "tags", kind_dir, "slabs.json"), slabs)
        tag(os.path.join(RES, "data", "minecraft", "tags", kind_dir, "stairs.json"), stairs)

    ores = [N + "coal_seam", N + "anthracite_ore", N + "deepslate_anthracite_ore"]
    for kind_dir in ("blocks", "items"):
        base = os.path.join(RES, "data", "forge", "tags", kind_dir)
        tag(os.path.join(base, "ores.json"), ores)
        tag(os.path.join(base, "ores", "coal.json"), [N + "coal_seam"])
        tag(os.path.join(base, "ores", "anthracite.json"), [N + "anthracite_ore", N + "deepslate_anthracite_ore"])
    tag(os.path.join(RES, "data", "forge", "tags", "items", "coal_coke.json"), [N + "coke"])
    # blocks the miners walk to and "work" at (MinerWorkGoal); data-driven so packs can extend it
    tag(os.path.join(DATA, "tags", "blocks", "miner_workstations.json"),
        [N + "coal_bunker", N + "coal_seam", N + "anthracite_ore", N + "deepslate_anthracite_ore",
         N + "mine_lamp", N + "ventilation_grate", "minecraft:coal_ore", "minecraft:deepslate_coal_ore",
         "minecraft:furnace", "minecraft:blast_furnace", "minecraft:anvil", "minecraft:grindstone",
         "minecraft:smithing_table", "minecraft:crafting_table"])
    tag(os.path.join(RES, "data", "forge", "tags", "items", "dusts", "coal.json"), [N + "coal_dust"])


# ------------------------------------------------------------------ lang ----
def gen_lang():
    from gen_sounds import lang_entries
    extra = dict(LANG_EXTRA)
    extra.update(lang_entries())
    langs = {"en_us": 0, "ru_ru": 1, "pl_pl": 2}
    for code, idx in langs.items():
        d = {}
        for b in BLOCKS:
            d[f"block.{MOD_ID}.{b['id']}"] = b["names"][idx]
        for it in ITEMS:
            d[f"item.{MOD_ID}.{it['id']}"] = it["names"][idx]
        for key, names in extra.items():
            d[key] = names[idx]
        wj(os.path.join(ASSETS, "lang", code + ".json"), d)


# ------------------------------------------------------------------ java ----
HEADER = ("// GENERATED by tools/gen_resources.py from tools/content.py - do not edit by hand.\n"
          "// Edit tools/content.py and re-run `python tools/gen_resources.py` instead.\n")


def java_props(b):
    color, hard, res, sound, tool, light = b["props"]
    p = (f"BlockBehaviour.Properties.of().mapColor(MapColor.{color})"
         f".strength({hard}F, {res}F).sound(SoundType.{sound})")
    if tool:
        p += ".requiresCorrectToolForDrops()"
    if light:
        p += f".lightLevel(state -> {light})"
    if b["kind"] in ("glass", "pane"):
        p += ".noOcclusion()"
    if b["kind"] == "glass":   # like vanilla glass: no suffocation, no view blocking, no mob spawns
        p += (".isValidSpawn((state, level, pos, type) -> false).isRedstoneConductor((state, level, pos) -> false)"
              ".isSuffocating((state, level, pos) -> false).isViewBlocking((state, level, pos) -> false)")
    return p


def gen_java():
    os.makedirs(JAVA, exist_ok=True)
    lines = [HEADER, "package com.donbass.mod.registry;\n",
             "import com.donbass.mod.DonbassMod;",
             "import java.util.function.Supplier;",
             "import net.minecraft.world.item.BlockItem;",
             "import net.minecraft.world.item.Item;",
             "import net.minecraft.world.level.block.Block;",
             "import net.minecraft.world.level.block.GlassBlock;",
             "import net.minecraft.world.level.block.IronBarsBlock;",
             "import net.minecraft.world.level.block.MagmaBlock;",
             "import net.minecraft.world.level.block.RotatedPillarBlock;",
             "import net.minecraft.world.level.block.SandBlock;",
             "import net.minecraft.world.level.block.SlabBlock;",
             "import net.minecraft.world.level.block.SoundType;",
             "import net.minecraft.world.level.block.StairBlock;",
             "import net.minecraft.world.level.block.state.BlockBehaviour;",
             "import net.minecraft.world.level.material.MapColor;",
             "import net.minecraftforge.registries.DeferredRegister;",
             "import net.minecraftforge.registries.ForgeRegistries;",
             "import net.minecraftforge.registries.RegistryObject;\n",
             "public final class ModBlocks {",
             "    public static final DeferredRegister<Block> BLOCKS =",
             "            DeferredRegister.create(ForgeRegistries.BLOCKS, DonbassMod.MOD_ID);\n",
             "    private ModBlocks() {}\n",
             "    private static RegistryObject<Block> register(String name, Supplier<Block> factory) {",
             "        RegistryObject<Block> block = BLOCKS.register(name, factory);",
             "        ModItems.ITEMS.register(name, () -> new BlockItem(block.get(), new Item.Properties()));",
             "        return block;",
             "    }\n"]
    for b in BLOCKS:
        i, k, const = b["id"], b["kind"], b["id"].upper()
        props = java_props(b)
        if k in ("cube",):
            ctor = f"new Block({props})"
        elif k == "pillar":
            ctor = f"new RotatedPillarBlock({props})"
        elif k == "slab":
            ctor = f"new SlabBlock({props})"
        elif k == "stairs":
            ctor = f"new StairBlock(() -> {b['base'].upper()}.get().defaultBlockState(), {props})"
        elif k == "pane":
            ctor = f"new IronBarsBlock({props})"
        elif k == "glass":
            ctor = f"new GlassBlock({props})"
        elif k == "falling":
            ctor = f"new SandBlock(0x{b['falling_color']:06X}, {props})"
        elif k == "magma":
            ctor = f"new MagmaBlock({props})"
        else:
            raise ValueError(k)
        lines.append(f"    public static final RegistryObject<Block> {const} =")
        lines.append(f"            register(\"{i}\", () -> {ctor});")
    lines.append("}")
    with open(os.path.join(JAVA, "ModBlocks.java"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    lines = [HEADER, "package com.donbass.mod.registry;\n",
             "import com.donbass.mod.DonbassMod;",
             "import com.donbass.mod.item.AkRifleItem;",
             "import com.donbass.mod.item.CombineSirenItem;",
             "import com.donbass.mod.item.DonbassArmorItem;",
             "import com.donbass.mod.item.FuelItem;",
             "import com.donbass.mod.item.ModTiers;",
             "import com.donbass.mod.item.TravelVoucherItem;",
             "import net.minecraft.world.food.FoodProperties;",
             "import net.minecraft.world.item.ArmorItem;",
             "import net.minecraft.world.item.Item;",
             "import net.minecraft.world.item.PickaxeItem;",
             "import net.minecraft.world.item.Rarity;",
             "import net.minecraftforge.common.ForgeSpawnEggItem;",
             "import net.minecraftforge.registries.DeferredRegister;",
             "import net.minecraftforge.registries.ForgeRegistries;",
             "import net.minecraftforge.registries.RegistryObject;\n",
             "public final class ModItems {",
             "    public static final DeferredRegister<Item> ITEMS =",
             "            DeferredRegister.create(ForgeRegistries.ITEMS, DonbassMod.MOD_ID);\n",
             "    private ModItems() {}\n"]
    for it in ITEMS:
        i, k, const = it["id"], it["kind"], it["id"].upper()
        if k == "plain":
            ctor = "new Item(new Item.Properties())"
        elif k == "fuel":
            ctor = f"new FuelItem({it['burn']}, new Item.Properties())"
        elif k == "food":
            ctor = (f"new Item(new Item.Properties().food(new FoodProperties.Builder()"
                    f".nutrition({it['nutrition']}).saturationMod({it['sat']}F).build()))")
        elif k == "ticket":
            ctor = "new TravelVoucherItem(new Item.Properties().stacksTo(16))"
        elif k == "pickaxe":
            tier = it.get("tier", "MINER")
            dmg, spd = it.get("attack_damage", 1), it.get("attack_speed", -2.8)
            extra = ".rarity(Rarity.EPIC).fireResistant()" if tier == "DIRECTOR" else ""
            ctor = f"new PickaxeItem(ModTiers.{tier}, {dmg}, {spd}F, new Item.Properties(){extra})"
        elif k == "siren":
            ctor = "new CombineSirenItem(new Item.Properties().stacksTo(1).rarity(Rarity.RARE))"
        elif k == "trophy":
            ctor = "new Item(new Item.Properties().stacksTo(1).rarity(Rarity.EPIC).fireResistant())"
        elif k == "rifle":
            ctor = "new AkRifleItem(new Item.Properties().stacksTo(1))"
        elif k == "armor":
            ctor = (f"new DonbassArmorItem(ModArmorMaterials.{it['mat']}, ArmorItem.Type.{it['slot']}, "
                    f"new Item.Properties())")
        elif k == "egg":
            bg, hl = it["colors"]
            ctor = f"new ForgeSpawnEggItem(ModEntities.{it['entity']}, 0x{bg:06X}, 0x{hl:06X}, new Item.Properties())"
        else:
            raise ValueError(k)
        lines.append(f"    public static final RegistryObject<Item> {const} =")
        lines.append(f"            ITEMS.register(\"{i}\", () -> {ctor});")
    lines.append("}")
    with open(os.path.join(JAVA, "ModItems.java"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main():
    for sub in ("blockstates", "models", "lang"):
        shutil.rmtree(os.path.join(ASSETS, sub), ignore_errors=True)
    shutil.rmtree(os.path.join(DATA, "loot_tables", "blocks"), ignore_errors=True)
    shutil.rmtree(os.path.join(DATA, "recipes"), ignore_errors=True)
    gen_block_assets()
    gen_item_assets()
    gen_loot()
    gen_recipes()
    gen_tags()
    gen_lang()
    gen_java()
    print(f"resources: {len(BLOCKS)} blocks, {len(ITEMS)} items, {len(RECIPES)} recipes")


if __name__ == "__main__":
    main()

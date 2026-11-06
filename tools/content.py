"""Single source of truth for blocks and items of the Donbass mod.

Everything else (Java registries, blockstates, models, loot tables, recipes,
tags, lang files) is generated from the tables in this file by gen_resources.py.
Names are (en, ru, pl).
"""

MOD_ID = "donbass"

# ---------------------------------------------------------------- blocks ----
# kind: cube | pillar | slab | stairs | pane | glass | falling | magma
# props: (mapColor, hardness, resistance, sound, needs_tool, light)
# tex:   cube -> "name";  pillar -> ("side", "end");  pane -> "name"
# loot:  "self" | ("ore", item, min, max, fortune)   (ore blocks give self with silk touch)
# tool:  pickaxe | shovel | axe ;  tier: None | stone | iron
BLOCKS = []


def block(id, names, kind="cube", tex=None, props=("STONE", 2.0, 6.0, "STONE", True, 0),
          loot="self", tool="pickaxe", tier=None, base=None, falling_color=None):
    BLOCKS.append(dict(id=id, names=names, kind=kind, tex=tex or id, props=props, loot=loot,
                       tool=tool, tier=tier, base=base, falling_color=falling_color))


# --- mine concrete & slag ---------------------------------------------------
block("mine_concrete", ("Mine Concrete", "Шахтный бетон", "Beton górniczy"),
      props=("COLOR_GRAY", 3.0, 9.0, "STONE", True, 0))
block("reinforced_mine_concrete", ("Reinforced Mine Concrete", "Армированный шахтный бетон", "Zbrojony beton górniczy"),
      props=("COLOR_GRAY", 5.0, 30.0, "STONE", True, 0), tier="stone")
block("cracked_mine_concrete", ("Cracked Mine Concrete", "Потрескавшийся шахтный бетон", "Popękany beton górniczy"),
      props=("COLOR_GRAY", 2.0, 5.0, "STONE", True, 0))
block("soot_stained_concrete", ("Soot-Stained Concrete", "Закопчённый бетон", "Okopcony beton"),
      props=("COLOR_BLACK", 3.0, 9.0, "STONE", True, 0))
block("mine_concrete_slab", ("Mine Concrete Slab", "Плита из шахтного бетона", "Płyta z betonu górniczego"),
      kind="slab", base="mine_concrete", props=("COLOR_GRAY", 3.0, 9.0, "STONE", True, 0))
block("mine_concrete_stairs", ("Mine Concrete Stairs", "Ступени из шахтного бетона", "Schody z betonu górniczego"),
      kind="stairs", base="mine_concrete", props=("COLOR_GRAY", 3.0, 9.0, "STONE", True, 0))

block("slag_block", ("Slag Block", "Шлакоблок", "Pustak żużlowy"),
      props=("COLOR_GRAY", 2.0, 6.0, "STONE", True, 0))
block("slag_bricks", ("Slag Bricks", "Шлаковый кирпич", "Cegły żużlowe"),
      props=("COLOR_GRAY", 2.0, 6.0, "STONE", True, 0))
block("polished_slag", ("Polished Slag", "Полированный шлак", "Polerowany żużel"),
      props=("COLOR_GRAY", 2.0, 6.0, "STONE", True, 0))
block("slag_bricks_slab", ("Slag Brick Slab", "Плита из шлакового кирпича", "Płyta z cegły żużlowej"),
      kind="slab", base="slag_bricks", props=("COLOR_GRAY", 2.0, 6.0, "STONE", True, 0))
block("slag_bricks_stairs", ("Slag Brick Stairs", "Ступени из шлакового кирпича", "Schody z cegły żużlowej"),
      kind="stairs", base="slag_bricks", props=("COLOR_GRAY", 2.0, 6.0, "STONE", True, 0))

# --- industrial & housing materials ----------------------------------------
block("sooty_bricks", ("Sooty Bricks", "Закопчённый кирпич", "Okopcone cegły"),
      props=("TERRACOTTA_BROWN", 2.0, 6.0, "STONE", True, 0))
block("whitewashed_wall", ("Whitewashed Wall", "Побелённая стена", "Bielona ściana"),
      props=("SNOW", 1.5, 4.0, "STONE", True, 0))
block("clay_plaster", ("Clay Plaster", "Глиняная обмазка", "Tynk gliniany"),
      props=("TERRACOTTA_YELLOW", 1.0, 3.0, "GRAVEL", False, 0), tool="shovel")
block("prefab_panel", ("Prefab Panel", "Панельная плита", "Płyta prefabrykowana"),
      props=("COLOR_LIGHT_GRAY", 3.0, 9.0, "STONE", True, 0))
block("slate_roof", ("Slate Roof Sheet", "Шифер", "Eternit falisty"),
      props=("COLOR_LIGHT_GRAY", 1.5, 4.0, "STONE", True, 0))
block("rusty_iron_block", ("Rusty Iron Block", "Ржавый железный блок", "Zardzewiały blok żelaza"),
      props=("COLOR_ORANGE", 4.0, 12.0, "METAL", True, 0))
block("rusty_plate", ("Rusty Plating", "Ржавая обшивка", "Zardzewiała blacha"),
      props=("COLOR_ORANGE", 3.0, 9.0, "METAL", True, 0))
block("factory_glass", ("Factory Glass", "Заводское стекло", "Szkło fabryczne"),
      kind="glass", props=("NONE", 0.4, 0.4, "GLASS", False, 0))
block("rusty_fence", ("Rusty Fence", "Ржавое ограждение", "Zardzewiałe ogrodzenie"),
      kind="pane", tex="rusty_fence", props=("COLOR_ORANGE", 2.0, 6.0, "METAL", True, 0))
block("chimney_bricks", ("Chimney Bricks", "Кирпич дымовой трубы", "Cegła kominowa"),
      props=("TERRACOTTA_RED", 2.0, 6.0, "STONE", True, 0))
block("hazard_stripes", ("Hazard Stripes", "Сигнальная разметка", "Oznakowanie ostrzegawcze"),
      props=("COLOR_YELLOW", 2.0, 6.0, "STONE", True, 0))
block("steel_girder", ("Steel Girder", "Стальная балка", "Dźwigar stalowy"),
      kind="pillar", tex=("steel_girder_side", "steel_girder_end"),
      props=("METAL", 4.0, 12.0, "METAL", True, 0))

# --- terricones & spoil -----------------------------------------------------
block("spoil_rock", ("Spoil Rock", "Порода терриконов", "Skała płonna"),
      props=("COLOR_GRAY", 1.5, 4.0, "STONE", True, 0))
block("burnt_spoil", ("Burnt Spoil", "Горелая порода", "Przepalona skała płonna"),
      props=("TERRACOTTA_RED", 1.5, 4.0, "STONE", True, 0))
block("spoil_gravel", ("Spoil Heap Gravel", "Отвальный щебень", "Żwir hałdowy"),
      kind="falling", props=("COLOR_GRAY", 0.7, 0.7, "GRAVEL", False, 0), tool="shovel", falling_color=0x3F3F3F)
block("coal_shale", ("Coal Shale", "Углистый сланец", "Łupek węglowy"),
      props=("COLOR_BLACK", 2.0, 5.0, "STONE", True, 0),
      loot=("ore", "coal_dust", 1, 2, True))
block("smoldering_spoil", ("Smoldering Spoil", "Тлеющая порода", "Tlący się odpad"),
      kind="magma", props=("COLOR_RED", 0.8, 0.8, "STONE", True, 6))

# --- ores -------------------------------------------------------------------
block("coal_seam", ("Coal Seam", "Угольный пласт", "Pokład węgla"),
      props=("STONE", 3.0, 3.0, "STONE", True, 0),
      loot=("ore", "minecraft:coal", 1, 3, True))
block("anthracite_ore", ("Anthracite Ore", "Антрацитовая руда", "Ruda antracytu"),
      props=("STONE", 3.5, 3.5, "STONE", True, 0), tier="stone",
      loot=("ore", "anthracite", 1, 2, True))
block("deepslate_anthracite_ore", ("Deepslate Anthracite Ore", "Глубинная антрацитовая руда", "Ruda antracytu w łupku głębinowym"),
      props=("DEEPSLATE", 4.5, 3.5, "DEEPSLATE", True, 0), tier="stone",
      loot=("ore", "anthracite", 1, 3, True))
block("anthracite_block", ("Block of Anthracite", "Антрацитовый блок", "Blok antracytu"),
      props=("COLOR_BLACK", 5.0, 6.0, "STONE", True, 0))
block("coke_block", ("Block of Coke", "Коксовый блок", "Blok koksu"),
      props=("COLOR_GRAY", 5.0, 6.0, "STONE", True, 0))
block("coal_bunker", ("Coal Bunker", "Угольный бункер", "Zasobnik węgla"),
      props=("METAL", 3.0, 6.0, "METAL", True, 0))

# --- mine equipment ---------------------------------------------------------
block("mine_timber_beam", ("Mine Timber Beam", "Шахтная стойка", "Stempel drewniany"),
      kind="pillar", tex=("mine_timber_beam_side", "mine_timber_beam_end"),
      props=("WOOD", 2.0, 3.0, "WOOD", False, 0), tool="axe")
block("mine_timber_planks", ("Mine Timber Planks", "Шахтный крепёжный лес", "Okładzina stemplowa"),
      props=("WOOD", 2.0, 3.0, "WOOD", False, 0), tool="axe")
block("mine_lamp", ("Mine Lamp", "Шахтный светильник", "Lampa górnicza"),
      props=("METAL", 1.0, 3.0, "METAL", False, 15))
block("ventilation_grate", ("Ventilation Grate", "Вентиляционная решётка", "Kratka wentylacyjna"),
      props=("METAL", 3.0, 6.0, "METAL", True, 0))

# --- railway ----------------------------------------------------------------
block("railway_ballast", ("Railway Ballast", "Железнодорожный балласт", "Podsypka kolejowa"),
      props=("COLOR_GRAY", 0.8, 0.8, "GRAVEL", False, 0), tool="shovel")
block("rail_sleepers", ("Rail Sleepers", "Шпалы", "Podkłady kolejowe"),
      kind="pillar", tex=("rail_sleepers_side", "rail_sleepers_end"),
      props=("COLOR_BROWN", 2.0, 3.0, "WOOD", False, 0), tool="axe")
block("freight_wagon_plating", ("Freight Wagon Plating", "Обшивка грузового вагона", "Poszycie wagonu towarowego"),
      props=("TERRACOTTA_RED", 3.0, 9.0, "METAL", True, 0))

# --- 0.3.0: the weapon workbench (opens a GUI; tex = (top, side, bottom)) --------------------------------
block("weapon_workbench", ("Weapon Workbench", "Оружейный верстак", "Warsztat zbrojeniowy"),
      kind="workbench", tex=("weapon_workbench_top", "weapon_workbench_side", "mine_concrete"),
      props=("METAL", 3.0, 6.0, "METAL", True, 0))

# ----------------------------------------------------------------- items ----
# kind: plain | food | fuel | ticket | pickaxe | rifle | armor | egg | akmod (mod -> AkMods.Mod constant)
#   armor -> mat (ModArmorMaterials constant), slot (HELMET|CHESTPLATE|LEGGINGS|BOOTS)
#   egg   -> entity (ModEntities constant), colors (background, highlight)
ITEMS = []


def item(id, names, kind="plain", burn=0, nutrition=0, sat=0.0, **extra):
    ITEMS.append(dict(id=id, names=names, kind=kind, burn=burn, nutrition=nutrition, sat=sat, **extra))


item("anthracite", ("Anthracite", "Антрацит", "Antracyt"), kind="fuel", burn=3200)
item("coke", ("Coke", "Кокс", "Koks"), kind="fuel", burn=2400)
item("coal_dust", ("Coal Dust", "Угольная пыль", "Pył węglowy"), kind="fuel", burn=400)
item("slag", ("Slag", "Шлак", "Żużel"))
item("iron_scrap", ("Iron Scrap", "Железный лом", "Złom żelaza"))
item("rusty_gear", ("Rusty Gear", "Ржавая шестерня", "Zardzewiałe koło zębate"))
item("miners_token", ("Miner's Token", "Жетон шахтёра", "Żeton górnika"))
item("miners_ration", ("Miner's Ration", "Шахтёрский паёк", "Racja górnika"), kind="food", nutrition=8, sat=0.8)
item("donbass_ticket", ("Donbass Travel Voucher", "Путёвка в Донбасс", "Skierowanie do Donbasu"), kind="ticket")
item("miners_pickaxe", ("Miner's Pickaxe", "Шахтёрская кирка", "Kilof górniczy"), kind="pickaxe")

# --- 0.2.0: firearms and components ------------------------------------------
item("rifle_cartridge", ("Rifle Rounds", "Патроны", "Naboje"))
item("rifle_magazine", ("Rifle Magazine", "Магазин для автомата", "Magazynek do karabinka"))
item("gun_parts", ("Weapon Parts", "Оружейные запчасти", "Części do broni"))
item("coal_plate", ("Coal Plate", "Угольная пластина", "Płyta węglowa"))
item("ak_rifle", ("AK Assault Rifle", "Автомат АК", "Karabinek AK"), kind="rifle")

# --- 0.3.0: AK modification kits (installed at the weapon workbench, see item/AkMods.java) --------------------
item("ak_mod_magazine", ("AK Extended Magazine Kit", "Комплект «Увеличенный магазин»", "Zestaw „Powiększony magazynek”"),
     kind="akmod", mod="MAGAZINE")
item("ak_mod_mechanism", ("AK Improved Reload Mechanism", "Улучшенный механизм перезарядки", "Ulepszony mechanizm przeładowania"),
     kind="akmod", mod="MECHANISM")
item("ak_mod_stabilizer", ("AK Stabilizer", "Стабилизатор для АК", "Stabilizator do AK"),
     kind="akmod", mod="STABILIZER")
item("ak_mod_barrel", ("AK Reinforced Barrel", "Усиленный ствол для АК", "Wzmocniona lufa do AK"),
     kind="akmod", mod="BARREL")
item("ak_mod_spring", ("AK Improved Spring", "Улучшенная пружина для АК", "Ulepszona sprężyna do AK"),
     kind="akmod", mod="SPRING")

# --- 0.2.0: armour (4 sets x 4 pieces) ----------------------------------------
HELMET, CHEST, LEGS, BOOTS = "HELMET", "CHESTPLATE", "LEGGINGS", "BOOTS"
ARMOR_SETS = {   # mat -> list of (id, names, slot)
    "MINERS": [
        ("miners_helmet", ("Miner's Hard Hat", "Шахтёрская каска", "Kask górnika"), HELMET),
        ("miners_jacket", ("Miner's Jacket", "Шахтёрская куртка", "Kurtka górnika"), CHEST),
        ("miners_trousers", ("Miner's Trousers", "Шахтёрские штаны", "Spodnie górnika"), LEGS),
        ("miners_boots", ("Miner's Boots", "Шахтёрские сапоги", "Buty górnika"), BOOTS)],
    "COAL": [
        ("coal_helmet", ("Coal Helmet", "Угольный шлем", "Hełm węglowy"), HELMET),
        ("coal_chestplate", ("Coal Chestplate", "Угольный нагрудник", "Napierśnik węglowy"), CHEST),
        ("coal_leggings", ("Coal Leggings", "Угольные поножи", "Nagolenniki węglowe"), LEGS),
        ("coal_boots", ("Coal Boots", "Угольные ботинки", "Buty węglowe"), BOOTS)],
    "STEPPE": [
        ("steppe_helmet", ("DPR Military Uniform Helmet", "Каска военной формы ДНР", "Hełm munduru wojskowego DRL"), HELMET),
        ("steppe_jacket", ("DPR Military Uniform Jacket", "Куртка военной формы ДНР", "Kurtka munduru wojskowego DRL"), CHEST),
        ("steppe_trousers", ("DPR Military Uniform Trousers", "Штаны военной формы ДНР", "Spodnie munduru wojskowego DRL"), LEGS),
        ("steppe_boots", ("DPR Military Uniform Boots", "Ботинки военной формы ДНР", "Buty munduru wojskowego DRL"), BOOTS)],
    "TERRICONE": [
        ("terricone_helmet", ("LPR Military Uniform Helmet", "Каска военной формы ЛНР", "Hełm munduru wojskowego ŁRL"), HELMET),
        ("terricone_jacket", ("LPR Military Uniform Jacket", "Куртка военной формы ЛНР", "Kurtka munduru wojskowego ŁRL"), CHEST),
        ("terricone_trousers", ("LPR Military Uniform Trousers", "Штаны военной формы ЛНР", "Spodnie munduru wojskowego ŁRL"), LEGS),
        ("terricone_boots", ("LPR Military Uniform Boots", "Ботинки военной формы ЛНР", "Buty munduru wojskowego ŁRL"), BOOTS)],
}
for _mat, _pieces in ARMOR_SETS.items():
    for _id, _names, _slot in _pieces:
        item(_id, _names, kind="armor", mat=_mat, slot=_slot)

# --- 0.2.0: spawn eggs ---------------------------------------------------------
item("miner_spawn_egg", ("Miner Spawn Egg", "Яйцо призыва: шахтёр", "Jajo przyzywające: górnik"),
     kind="egg", entity="MINER", colors=(0x6E5B3A, 0xD9A441))
item("north_fighter_spawn_egg", ("DPR Militiaman Spawn Egg", "Яйцо призыва: Ополченец ДНР",
                                 "Jajo przyzywające: Milicjant DRL"),
     kind="egg", entity="NORTH_FIGHTER", colors=(0x8A8460, 0xF2F2F2))
item("south_fighter_spawn_egg", ("LPR Militiaman Spawn Egg", "Яйцо призыва: Ополченец ЛНР",
                                 "Jajo przyzywające: Milicjant ŁRL"),
     kind="egg", entity="SOUTH_FIGHTER", colors=(0x3A3C40, 0xE07B22))

# --- 0.2.0: the boss ("Combine Director", fictional) and what it leaves behind ---------------------------
item("combine_siren", ("Coal Region Chairman's Siren", "Сирена Председателя Угольного края",
                       "Syrena Przewodniczącego Kraju Węglowego"), kind="siren")
item("director_pickaxe", ("Coal Region Chairman's Pickaxe", "Именная кирка Председателя Угольного края",
                          "Imienny kilof Przewodniczącego Kraju Węglowego"),
     kind="pickaxe", tier="DIRECTOR", attack_damage=2, attack_speed=-2.6)
item("director_badge", ("Coal Region Chairman's Badge of Merit", "Знак отличия Председателя Угольного края",
                        "Odznaka zasługi Przewodniczącego Kraju Węglowego"),
     kind="trophy")

# creative tab / misc keys
LANG_EXTRA = {
    "itemGroup.donbass": ("Donbass", "Донбасс", "Donbas"),
    "biome.donbass.steppe": ("Donbass Steppe", "Донбасская степь", "Step donbaski"),
    "biome.donbass.balka": ("Balka Gully", "Балка", "Bałka (jar stepowy)"),
    "message.donbass.travel_to": ("The steppe wind carries you to the Donbass...", "Степной ветер несёт вас на Донбасс...", "Stepowy wiatr niesie cię do Donbasu..."),
    "message.donbass.travel_back": ("You return from the Donbass.", "Вы возвращаетесь с Донбасса.", "Wracasz z Donbasu."),
    "message.donbass.wrong_place": ("The voucher only works in the Overworld and in the Donbass.", "Путёвка действует только в Верхнем мире и на Донбассе.", "Skierowanie działa tylko w Nadświecie i w Donbasie."),
}

# recipes (raw JSON dicts keyed by file name); "donbass:" prefix added where needed
D = "donbass:"
RECIPES = {
    "mine_concrete": {"type": "minecraft:crafting_shaped", "pattern": ["CS", "SC"],
                      "key": {"C": {"item": "minecraft:cobblestone"}, "S": {"item": D + "slag"}},
                      "result": {"item": D + "mine_concrete", "count": 4}},
    "reinforced_mine_concrete": {"type": "minecraft:crafting_shapeless",
                                 "ingredients": [{"item": D + "mine_concrete"}] * 4 + [{"item": "minecraft:iron_ingot"}],
                                 "result": {"item": D + "reinforced_mine_concrete", "count": 4}},
    "cracked_mine_concrete": {"type": "minecraft:smelting", "ingredient": {"item": D + "mine_concrete"},
                              "result": D + "cracked_mine_concrete", "experience": 0.1, "cookingtime": 200},
    "soot_stained_concrete": {"type": "minecraft:crafting_shapeless",
                              "ingredients": [{"item": D + "mine_concrete"}, {"item": D + "coal_dust"}],
                              "result": {"item": D + "soot_stained_concrete", "count": 1}},
    "slag_from_spoil": {"type": "minecraft:smelting", "ingredient": {"item": D + "spoil_rock"},
                        "result": D + "slag", "experience": 0.1, "cookingtime": 200},
    "slag_from_burnt_spoil": {"type": "minecraft:smelting", "ingredient": {"item": D + "burnt_spoil"},
                              "result": D + "slag", "experience": 0.1, "cookingtime": 200},
    "slag_block": {"type": "minecraft:crafting_shaped", "pattern": ["SS", "SS"],
                   "key": {"S": {"item": D + "slag"}}, "result": {"item": D + "slag_block", "count": 4}},
    "slag_bricks": {"type": "minecraft:crafting_shaped", "pattern": ["BB", "BB"],
                    "key": {"B": {"item": D + "slag_block"}}, "result": {"item": D + "slag_bricks", "count": 4}},
    "polished_slag": {"type": "minecraft:crafting_shaped", "pattern": ["BB", "BB"],
                      "key": {"B": {"item": D + "slag_bricks"}}, "result": {"item": D + "polished_slag", "count": 4}},
    "mine_concrete_slab": {"type": "minecraft:crafting_shaped", "pattern": ["CCC"],
                           "key": {"C": {"item": D + "mine_concrete"}}, "result": {"item": D + "mine_concrete_slab", "count": 6}},
    "mine_concrete_stairs": {"type": "minecraft:crafting_shaped", "pattern": ["C  ", "CC ", "CCC"],
                             "key": {"C": {"item": D + "mine_concrete"}}, "result": {"item": D + "mine_concrete_stairs", "count": 4}},
    "slag_bricks_slab": {"type": "minecraft:crafting_shaped", "pattern": ["CCC"],
                         "key": {"C": {"item": D + "slag_bricks"}}, "result": {"item": D + "slag_bricks_slab", "count": 6}},
    "slag_bricks_stairs": {"type": "minecraft:crafting_shaped", "pattern": ["C  ", "CC ", "CCC"],
                           "key": {"C": {"item": D + "slag_bricks"}}, "result": {"item": D + "slag_bricks_stairs", "count": 4}},
    "sooty_bricks": {"type": "minecraft:crafting_shapeless",
                     "ingredients": [{"item": "minecraft:bricks"}, {"item": D + "coal_dust"}],
                     "result": {"item": D + "sooty_bricks", "count": 1}},
    "whitewashed_wall": {"type": "minecraft:crafting_shapeless",
                         "ingredients": [{"item": D + "clay_plaster"}, {"item": "minecraft:bone_meal"}],
                         "result": {"item": D + "whitewashed_wall", "count": 1}},
    "clay_plaster": {"type": "minecraft:crafting_shaped", "pattern": ["CC", "CC"],
                     "key": {"C": {"item": "minecraft:clay_ball"}}, "result": {"item": D + "clay_plaster", "count": 4}},
    "prefab_panel": {"type": "minecraft:crafting_shaped", "pattern": ["CIC", "CCC"],
                     "key": {"C": {"item": D + "mine_concrete"}, "I": {"item": "minecraft:iron_nugget"}},
                     "result": {"item": D + "prefab_panel", "count": 4}},
    "slate_roof": {"type": "minecraft:crafting_shaped", "pattern": ["SSS"],
                   "key": {"S": {"item": D + "polished_slag"}}, "result": {"item": D + "slate_roof", "count": 6}},
    "rusty_iron_block": {"type": "minecraft:crafting_shaped", "pattern": ["SSS", "SSS", "SSS"],
                         "key": {"S": {"item": D + "iron_scrap"}}, "result": {"item": D + "rusty_iron_block", "count": 1}},
    "rusty_plate": {"type": "minecraft:crafting_shapeless",
                    "ingredients": [{"item": D + "rusty_iron_block"}],
                    "result": {"item": D + "rusty_plate", "count": 4}},
    "factory_glass": {"type": "minecraft:crafting_shaped", "pattern": ["GI", "IG"],
                      "key": {"G": {"item": "minecraft:glass"}, "I": {"item": "minecraft:iron_nugget"}},
                      "result": {"item": D + "factory_glass", "count": 4}},
    "rusty_fence": {"type": "minecraft:crafting_shaped", "pattern": ["SSS", "SSS"],
                    "key": {"S": {"item": D + "iron_scrap"}}, "result": {"item": D + "rusty_fence", "count": 8}},
    "chimney_bricks": {"type": "minecraft:crafting_shapeless",
                       "ingredients": [{"item": D + "sooty_bricks"}, {"item": "minecraft:white_concrete_powder"}],
                       "result": {"item": D + "chimney_bricks", "count": 1}},
    "hazard_stripes": {"type": "minecraft:crafting_shapeless",
                       "ingredients": [{"item": D + "mine_concrete"}, {"item": "minecraft:yellow_dye"}, {"item": "minecraft:black_dye"}],
                       "result": {"item": D + "hazard_stripes", "count": 2}},
    "steel_girder": {"type": "minecraft:crafting_shaped", "pattern": ["III", " I ", "III"],
                     "key": {"I": {"item": "minecraft:iron_ingot"}}, "result": {"item": D + "steel_girder", "count": 4}},
    "coal_dust": {"type": "minecraft:crafting_shapeless",
                  "ingredients": [{"item": "minecraft:coal"}], "result": {"item": D + "coal_dust", "count": 2}},
    "coke": {"type": "minecraft:smelting", "ingredient": {"item": "minecraft:coal"},
             "result": D + "coke", "experience": 0.35, "cookingtime": 400},
    "coke_blasting": {"type": "minecraft:blasting", "ingredient": {"item": "minecraft:coal"},
                      "result": D + "coke", "experience": 0.35, "cookingtime": 200},
    "coke_block": {"type": "minecraft:crafting_shaped", "pattern": ["CCC", "CCC", "CCC"],
                   "key": {"C": {"item": D + "coke"}}, "result": {"item": D + "coke_block", "count": 1}},
    "coke_from_block": {"type": "minecraft:crafting_shapeless", "ingredients": [{"item": D + "coke_block"}],
                        "result": {"item": D + "coke", "count": 9}},
    "anthracite_block": {"type": "minecraft:crafting_shaped", "pattern": ["AAA", "AAA", "AAA"],
                         "key": {"A": {"item": D + "anthracite"}}, "result": {"item": D + "anthracite_block", "count": 1}},
    "anthracite_from_block": {"type": "minecraft:crafting_shapeless", "ingredients": [{"item": D + "anthracite_block"}],
                              "result": {"item": D + "anthracite", "count": 9}},
    "anthracite_ore_smelting": {"type": "minecraft:smelting", "ingredient": {"item": D + "anthracite_ore"},
                                "result": D + "anthracite", "experience": 0.2, "cookingtime": 200},
    "anthracite_ore_blasting": {"type": "minecraft:blasting", "ingredient": {"item": D + "anthracite_ore"},
                                "result": D + "anthracite", "experience": 0.2, "cookingtime": 100},
    "deepslate_anthracite_ore_smelting": {"type": "minecraft:smelting", "ingredient": {"item": D + "deepslate_anthracite_ore"},
                                          "result": D + "anthracite", "experience": 0.2, "cookingtime": 200},
    "deepslate_anthracite_ore_blasting": {"type": "minecraft:blasting", "ingredient": {"item": D + "deepslate_anthracite_ore"},
                                          "result": D + "anthracite", "experience": 0.2, "cookingtime": 100},
    "coal_bunker": {"type": "minecraft:crafting_shaped", "pattern": ["I I", "ICI", "III"],
                    "key": {"I": {"item": "minecraft:iron_ingot"}, "C": {"item": "minecraft:coal_block"}},
                    "result": {"item": D + "coal_bunker", "count": 1}},
    "mine_timber_beam": {"type": "minecraft:crafting_shaped", "pattern": ["L", "L"],
                         "key": {"L": {"item": "minecraft:spruce_log"}}, "result": {"item": D + "mine_timber_beam", "count": 3}},
    "mine_timber_planks": {"type": "minecraft:crafting_shapeless",
                           "ingredients": [{"item": D + "mine_timber_beam"}],
                           "result": {"item": D + "mine_timber_planks", "count": 2}},
    "mine_lamp": {"type": "minecraft:crafting_shaped", "pattern": [" I ", "GTG", " I "],
                  "key": {"I": {"item": "minecraft:iron_ingot"}, "G": {"item": "minecraft:glass_pane"}, "T": {"item": "minecraft:torch"}},
                  "result": {"item": D + "mine_lamp", "count": 2}},
    "ventilation_grate": {"type": "minecraft:crafting_shaped", "pattern": ["IGI", "GIG", "IGI"],
                          "key": {"I": {"item": "minecraft:iron_ingot"}, "G": {"item": D + "rusty_fence"}},
                          "result": {"item": D + "ventilation_grate", "count": 2}},
    "railway_ballast": {"type": "minecraft:crafting_shapeless",
                        "ingredients": [{"item": "minecraft:gravel"}, {"item": D + "slag"}],
                        "result": {"item": D + "railway_ballast", "count": 2}},
    "rail_sleepers": {"type": "minecraft:crafting_shaped", "pattern": ["L", "L"],
                      "key": {"L": {"item": D + "mine_timber_beam"}}, "result": {"item": D + "rail_sleepers", "count": 2}},
    "freight_wagon_plating": {"type": "minecraft:crafting_shaped", "pattern": ["RR", "RR"],
                              "key": {"R": {"item": D + "rusty_plate"}}, "result": {"item": D + "freight_wagon_plating", "count": 4}},
    "miners_ration": {"type": "minecraft:crafting_shapeless",
                      "ingredients": [{"item": "minecraft:bread"}, {"item": "minecraft:cooked_porkchop"}, {"item": "minecraft:beetroot"}],
                      "result": {"item": D + "miners_ration", "count": 1}},
    "iron_from_scrap": {"type": "minecraft:smelting", "ingredient": {"item": D + "iron_scrap"},
                        "result": "minecraft:iron_nugget", "experience": 0.05, "cookingtime": 100},
    "iron_from_scrap_blasting": {"type": "minecraft:blasting", "ingredient": {"item": D + "iron_scrap"},
                                 "result": "minecraft:iron_nugget", "experience": 0.05, "cookingtime": 50},
    "iron_from_gear": {"type": "minecraft:smelting", "ingredient": {"item": D + "rusty_gear"},
                       "result": "minecraft:iron_ingot", "experience": 0.3, "cookingtime": 200},
    "miners_token": {"type": "minecraft:crafting_shapeless",
                     "ingredients": [{"item": "minecraft:iron_nugget"}, {"item": "minecraft:iron_nugget"},
                                     {"item": "minecraft:gold_nugget"}],
                     "result": {"item": D + "miners_token", "count": 2}},
    "miners_pickaxe": {"type": "minecraft:crafting_shaped", "pattern": ["CAC", " S ", " S "],
                       "key": {"C": {"item": D + "coke"}, "A": {"item": D + "anthracite"},
                               "S": {"item": "minecraft:stick"}},
                       "result": {"item": D + "miners_pickaxe", "count": 1}},
    "donbass_ticket": {"type": "minecraft:crafting_shapeless",
                       "ingredients": [{"item": "minecraft:paper"}, {"item": "minecraft:coal"}, {"item": D + "miners_token"}],
                       "result": {"item": D + "donbass_ticket", "count": 1}},
}


# ---- 0.2.0 recipes: every recipe below is a game convention, not a real-world manufacturing guide ----
def _shaped(pattern, key, result, count=1):
    keys = {k: ({"tag": v[1:]} if v.startswith("#") else {"item": v}) for k, v in key.items()}
    return {"type": "minecraft:crafting_shaped", "pattern": pattern, "key": keys,
            "result": {"item": result, "count": count}}


def _shapeless(ingredients, result, count=1):
    return {"type": "minecraft:crafting_shapeless", "ingredients": [{"item": i} for i in ingredients],
            "result": {"item": result, "count": count}}


V = "minecraft:"
RECIPES.update({
    "rifle_cartridge": _shapeless([V + "copper_ingot", V + "gunpowder", V + "iron_nugget"], D + "rifle_cartridge", 8),
    "gun_parts": _shapeless([V + "iron_ingot", V + "iron_ingot", V + "redstone", D + "rusty_gear"], D + "gun_parts", 1),
    "gun_parts_from_scrap": _shapeless([D + "iron_scrap"] * 4 + [V + "redstone"], D + "gun_parts", 1),
    "rifle_magazine": _shaped(["I I", "IPI", "III"], {"I": V + "iron_ingot", "P": D + "gun_parts"}, D + "rifle_magazine"),
    "ak_rifle": _shaped(["GIP", "PMI", "W  "], {"G": D + "steel_girder", "I": V + "iron_ingot", "P": D + "gun_parts",
                                                "M": D + "rifle_magazine", "W": "#minecraft:planks"}, D + "ak_rifle"),
    "coal_plate": _shapeless([V + "iron_ingot", D + "anthracite", D + "anthracite", D + "coke"], D + "coal_plate", 2),
    # miner's work clothes (leather + a little iron): the cheap, early set
    "miners_helmet": _shaped(["LML", "L L"], {"L": V + "leather", "M": D + "mine_lamp"}, D + "miners_helmet"),
    "miners_jacket": _shaped(["L L", "LDL", "LLL"], {"L": V + "leather", "D": D + "coal_dust"}, D + "miners_jacket"),
    "miners_trousers": _shaped(["LLL", "L L", "L L"], {"L": V + "leather"}, D + "miners_trousers"),
    "miners_boots": _shaped(["N N", "L L"], {"N": V + "iron_nugget", "L": V + "leather"}, D + "miners_boots"),
    # coal armour: coal plates in the vanilla armour shapes
    "coal_helmet": _shaped(["PPP", "P P"], {"P": D + "coal_plate"}, D + "coal_helmet"),
    "coal_chestplate": _shaped(["P P", "PPP", "PPP"], {"P": D + "coal_plate"}, D + "coal_chestplate"),
    "coal_leggings": _shaped(["PPP", "P P", "P P"], {"P": D + "coal_plate"}, D + "coal_leggings"),
    "coal_boots": _shaped(["P P", "P P"], {"P": D + "coal_plate"}, D + "coal_boots"),
    # field uniforms: only helmets and boots can be made; jackets and trousers come from loot, drops and trade
    "steppe_helmet": _shapeless([V + "leather_helmet", V + "iron_ingot", V + "green_dye"], D + "steppe_helmet"),
    "steppe_boots": _shapeless([V + "leather_boots", V + "iron_nugget", V + "iron_nugget", V + "green_dye"], D + "steppe_boots"),
    "terricone_helmet": _shapeless([V + "leather_helmet", V + "iron_ingot", V + "black_dye"], D + "terricone_helmet"),
    "terricone_boots": _shapeless([V + "leather_boots", V + "iron_nugget", V + "iron_nugget", V + "black_dye"], D + "terricone_boots"),
    # the siren that calls the boss (0.4.0: a much more expensive recipe; the administration building still holds one
    # in a chest).  Only things the player finds or makes in the Donbass before the first fight (never the boss's own
    # badge or pickaxe): coal plates (deep mines, factories, sergeants; or iron + 2 anthracite + coke), rifle magazines
    # (checkpoints, factories, fighters; or 7 iron + weapon parts), an anthracite block (9 anthracite from the ore or the
    # mine chests), weapon parts (fighters, checkpoints, mines; or a rusty gear / 4 iron scrap + iron + redstone),
    # plus a vanilla bell and a diamond (also in the deep mine chests).  tools/validate.py check_siren_recipe.
    "combine_siren": _shaped(["PBP", "MAM", "GDG"], {"P": D + "coal_plate", "B": V + "bell", "M": D + "rifle_magazine",
                                                     "A": D + "anthracite_block", "G": D + "gun_parts",
                                                     "D": V + "diamond"}, D + "combine_siren"),
})

# ---- 0.2.0 lang (en, ru, pl) -----------------------------------------------------
LANG_EXTRA.update({
    "entity.donbass.miner": ("Miner", "Шахтёр", "Górnik"),
    "entity.donbass.north_fighter": ("DPR Militiaman", "Ополченец ДНР", "Milicjant DRL"),
    "entity.donbass.south_fighter": ("LPR Militiaman", "Ополченец ЛНР", "Milicjant ŁRL"),
    "tooltip.donbass.rifle_ammo": ("Rounds: %s / %s", "Патронов: %s / %s", "Naboje: %s / %s"),
    "tooltip.donbass.rifle_hint": ("Hold Use to fire, Shift + Use to reload", "Удерживайте ПКМ для стрельбы, Shift + ПКМ — перезарядка",
                                   "Przytrzymaj PPM, aby strzelać; Shift + PPM — przeładowanie"),
    "tooltip.donbass.rifle_reloading": ("Reloading...", "Перезарядка...", "Przeładowanie..."),
    "message.donbass.rifle_no_ammo": ("Out of rounds", "Нет патронов", "Brak naboi"),
    "message.donbass.rifle_empty_mag": ("Magazine empty - reloading", "Магазин пуст — перезарядка", "Magazynek pusty — przeładowanie"),
    "message.donbass.rifle_full": ("Magazine is full", "Магазин полон", "Magazynek jest pełny"),
    "tooltip.donbass.set_coal": ("Full set: fire and lava resistance, tougher against blasts",
                                 "Полный комплект: огнестойкость и защита от лавы, лучше держит взрывы",
                                 "Pełny komplet: odporność na ogień i lawę, lepsza ochrona przed wybuchami"),
    "tooltip.donbass.set_miners": ("Full set: more mining speed underground", "Полный комплект: быстрее копать под землёй",
                                   "Pełny komplet: szybsze kopanie pod ziemią"),
    "tooltip.donbass.set_field": ("Military uniform: dropped by militiamen and found at checkpoints",
                                  "Военная форма: выпадает из ополченцев и лежит на блокпостах",
                                  "Mundur wojskowy: wypada z milicjantów i leży na posterunkach"),
    "message.donbass.miner_hostile": ("The miner refuses to trade with you.", "Шахтёр не хочет с вами торговать.",
                                      "Górnik nie chce z tobą handlować."),
    "message.donbass.coal_set_on": ("The coal armour set protects you from fire.", "Угольный комплект защищает вас от огня.",
                                    "Zbroja węglowa chroni cię przed ogniem."),
    "entity.donbass.combine_director": ("Chairman of the Coal Region", "Председатель Угольного края",
                                        "Przewodniczący Kraju Węglowego"),
    "boss.donbass.phase1": ("Phase I: The Briefing", "Фаза I: Планёрка", "Faza I: Odprawa"),
    "boss.donbass.phase2": ("Phase II: All Hands", "Фаза II: Аврал", "Faza II: Wszyscy na pokład"),
    "boss.donbass.phase3": ("Phase III: Fire in the Face", "Фаза III: Пожар в забое", "Faza III: Pożar w przodku"),
    "message.donbass.director_summon": ("The siren wails. The Chairman of the Coal Region has come to see who is making the noise.",
                                        "Воет сирена. Председатель Угольного края вышел узнать, кто тут шумит.",
                                        "Syrena wyje. Przewodniczący Kraju Węglowego wyszedł sprawdzić, kto tu hałasuje."),
    "message.donbass.director_phase2": ("\"Everyone to the shift! Overtime for the lot of you!\"",
                                        "«Все на смену! Сверхурочные — каждому!»",
                                        "„Wszyscy na zmianę! Nadgodziny dla każdego!”"),
    "message.donbass.director_phase3": ("\"The plan will be met, even over your dead bodies!\"",
                                        "«План будет выполнен — хоть через ваши трупы!»",
                                        "„Plan zostanie wykonany, nawet po waszych trupach!”"),
    "message.donbass.director_defeated": ("The Chairman of the Coal Region is down. The shift is over.",
                                          "Председатель Угольного края повержен. Смена окончена.",
                                          "Przewodniczący Kraju Węglowego pokonany. Zmiana skończona."),
    "message.donbass.siren_busy": ("The Chairman of the Coal Region is already here, or somebody called him a moment ago.",
                                   "Председатель Угольного края уже здесь — или его только что вызвали.",
                                   "Przewodniczący Kraju Węglowego już tu jest albo ktoś właśnie go wezwał."),
    "message.donbass.siren_peaceful": ("The siren stays silent on Peaceful difficulty.",
                                       "На мирной сложности сирена молчит.",
                                       "Na poziomie pokojowym syrena milczy."),
    "message.donbass.siren_no_room": ("There is not enough open space here to call the Chairman of the Coal Region.",
                                      "Здесь слишком тесно, чтобы вызвать Председателя Угольного края.",
                                      "Jest tu zbyt ciasno, by wezwać Przewodniczącego Kraju Węglowego."),
    "tooltip.donbass.siren": ("Use on open ground to call the Chairman of the Coal Region (boss). Consumed on use.",
                              "ПКМ на открытой местности вызывает Председателя Угольного края (босс). Расходуется.",
                              "PPM na otwartym terenie wzywa Przewodniczącego Kraju Węglowego (boss). Zużywa się."),
    "tooltip.donbass.siren_hint": ("Bring armour, plenty of rounds and friends.",
                                   "Берите броню, много патронов и друзей.",
                                   "Zabierz zbroję, dużo naboi i przyjaciół."),
    "tooltip.donbass.director_pickaxe": ("Unique reward. Mines fast; repaired with coal plates.",
                                         "Уникальная награда. Копает быстро; чинится угольными пластинами.",
                                         "Unikalna nagroda. Szybko kopie; naprawa płytami węglowymi."),
    "tooltip.donbass.director_badge": ("A trophy: proof that the shift was survived.",
                                       "Трофей: доказательство того, что смена пережита.",
                                       "Trofeum: dowód, że zmianę udało się przetrwać."),
})

# ---- 0.3.0: weapon workbench and AK modifications (game conventions, not manufacturing instructions) ----
RECIPES.update({
    "weapon_workbench": _shaped(["GGG", "PTP", "I I"], {"G": D + "steel_girder", "P": D + "gun_parts",
                                                        "T": V + "crafting_table", "I": V + "iron_ingot"},
                                D + "weapon_workbench"),
    "ak_mod_magazine": _shapeless([D + "rifle_magazine", D + "gun_parts", V + "iron_ingot", V + "iron_ingot"],
                                  D + "ak_mod_magazine"),
    "ak_mod_mechanism": _shapeless([D + "gun_parts", D + "gun_parts", V + "redstone", V + "redstone", D + "rusty_gear"],
                                   D + "ak_mod_mechanism"),
    "ak_mod_stabilizer": _shapeless([D + "steel_girder", D + "gun_parts", V + "redstone", V + "iron_ingot"],
                                    D + "ak_mod_stabilizer"),
    "ak_mod_barrel": _shapeless([D + "coal_plate", D + "coal_plate", D + "steel_girder", D + "gun_parts"],
                                D + "ak_mod_barrel"),
    "ak_mod_spring": _shapeless([V + "iron_ingot", V + "iron_ingot", V + "redstone", D + "coke", D + "gun_parts"],
                                D + "ak_mod_spring"),
})

# "%%" is a literal percent sign in Minecraft translation strings
LANG_EXTRA.update({
    "tooltip.donbass.ak_mod_magazine": ("+50%% magazine capacity (loaded rounds are kept)",
                                        "+50%% к вместимости магазина (заряженные патроны сохраняются)",
                                        "+50%% pojemności magazynka (załadowane naboje zostają)"),
    "tooltip.donbass.ak_mod_mechanism": ("-20%% reload time", "−20%% ко времени перезарядки",
                                         "-20%% czasu przeładowania"),
    "tooltip.donbass.ak_mod_stabilizer": ("-20%% bullet spread", "−20%% к разбросу пуль", "-20%% rozrzutu pocisków"),
    "tooltip.donbass.ak_mod_barrel": ("-10%% bullet spread (damage is unchanged)",
                                      "−10%% к разбросу пуль (урон не меняется)",
                                      "-10%% rozrzutu pocisków (obrażenia bez zmian)"),
    "tooltip.donbass.ak_mod_spring": ("+10%% rate of fire", "+10%% к скорострельности", "+10%% szybkostrzelności"),
    "tooltip.donbass.ak_mod_install": ("Install at a Weapon Workbench; one of each kind per rifle.",
                                       "Устанавливается на оружейном верстаке; каждый вид — один раз на автомат.",
                                       "Montuje się w warsztacie zbrojeniowym; każdy rodzaj raz na karabinek."),
    "tooltip.donbass.rifle_mods": ("Modifications:", "Модификации:", "Modyfikacje:"),
    "gui.donbass.workbench.install": ("Install", "Установить", "Zainstaluj"),
    "gui.donbass.workbench.duplicate": ("Already installed", "Уже установлено", "Już zainstalowano"),
    "gui.donbass.workbench.hint": ("Put the AK and kits into the slots, then press Install.",
                                   "Положите АК и комплекты в слоты, затем нажмите «Установить».",
                                   "Włóż AK i zestawy do slotów, potem naciśnij „Zainstaluj”."),
    "gui.donbass.workbench.installed": ("Installed", "Установлено", "Zainstalowano"),
    "gui.donbass.workbench.not_installed": ("Not installed", "Не установлено", "Nie zainstalowano"),
    "gui.donbass.workbench.stat.magazine": ("Magazine", "Магазин", "Magazynek"),
    "gui.donbass.workbench.stat.reload": ("Reload", "Перезарядка", "Przeładowanie"),
    "gui.donbass.workbench.stat.rate": ("Rate of fire", "Скорострельность", "Szybkostrzelność"),
    "gui.donbass.workbench.stat.spread": ("Spread", "Разброс", "Rozrzut"),
    "gui.donbass.workbench.unit.rounds": ("%s rounds", "%s патр.", "%s nab."),
    "gui.donbass.workbench.unit.seconds": ("%s s", "%s с", "%s s"),
    "gui.donbass.workbench.unit.rpm": ("%s rpm", "%s в/мин", "%s/min"),
    "gui.donbass.workbench.unit.degrees": ("%s°", "%s°", "%s°"),
    "gui.donbass.workbench.mod.magazine": ("Extended magazine", "Увеличенный магазин", "Powiększony magazynek"),
    "gui.donbass.workbench.mod.mechanism": ("Improved mechanism", "Улучшенный механизм", "Ulepszony mechanizm"),
    "gui.donbass.workbench.mod.stabilizer": ("Stabilizer", "Стабилизатор", "Stabilizator"),
    "gui.donbass.workbench.mod.barrel": ("Reinforced barrel", "Усиленный ствол", "Wzmocniona lufa"),
    "gui.donbass.workbench.mod.spring": ("Improved spring", "Улучшенная пружина", "Ulepszona sprężyna"),
    "gui.donbass.workbench.chip.magazine": ("Mag", "Маг", "Mag"),
    "gui.donbass.workbench.chip.mechanism": ("Mec", "Мех", "Mec"),
    "gui.donbass.workbench.chip.stabilizer": ("Stb", "Стб", "Stb"),
    "gui.donbass.workbench.chip.barrel": ("Brl", "Ств", "Luf"),
    "gui.donbass.workbench.chip.spring": ("Spr", "Пру", "Spr"),
    "message.donbass.workbench_installed": ("Installed: %s", "Установлено: %s", "Zainstalowano: %s"),
})

# ---- 0.4.0 lang: the commands /donbass bosshp and /donbasshelp (en, ru, pl) -------------------------------
# Notes: a literal percent sign in a lang value is written "%%" (the game's formatter reads "% " followed by a letter as
# a placeholder); %1$s... are the arguments passed by DonbassCommands (see the comments there): bosshp.current / .set get
# (multiplier, health), bosshp.usage gets (min, max), the error texts get (typed text, min, max).
LANG_EXTRA.update({
    "command.donbass.usage": (
        "Donbass commands: /donbasshelp - the guide; /donbass bosshp [multiplier] - the boss health multiplier.",
        "Команды Донбасса: /donbasshelp — справка; /donbass bosshp [множитель] — множитель здоровья босса.",
        "Komendy Donbasu: /donbasshelp – poradnik; /donbass bosshp [mnożnik] – mnożnik zdrowia bossa."),
    "command.donbass.bosshp.current": (
        "Boss health multiplier: x%1$s (a new boss gets %2$s HP).",
        "Множитель здоровья босса: ×%1$s (новый босс получит %2$s HP).",
        "Mnożnik zdrowia bossa: ×%1$s (nowy boss dostanie %2$s HP)."),
    "command.donbass.bosshp.usage": (
        "Usage: /donbass bosshp <multiplier> - a number with a decimal point from %1$s to %2$s, for example 1.5 (operators only).",
        "Синтаксис: /donbass bosshp <множитель> — число через точку от %1$s до %2$s, например 1.5 (только для операторов).",
        "Składnia: /donbass bosshp <mnożnik> – liczba z kropką dziesiętną od %1$s do %2$s, np. 1.5 (tylko dla operatorów)."),
    "command.donbass.bosshp.set": (
        "Boss health multiplier set to x%1$s: the next boss will have %2$s HP. A boss that already stands is not changed.",
        "Множитель здоровья босса: ×%1$s. Следующий босс получит %2$s HP; уже стоящий босс не меняется.",
        "Mnożnik zdrowia bossa ustawiony na ×%1$s. Następny boss dostanie %2$s HP; boss, który już stoi, się nie zmienia."),
    "command.donbass.bosshp.no_permission": (
        "Only operators (OP) can change the boss health multiplier. Read it with /donbass bosshp, the guide is /donbasshelp.",
        "Менять множитель здоровья босса могут только операторы (OP). Посмотреть его можно командой /donbass bosshp, справка — /donbasshelp.",
        "Mnożnik zdrowia bossa mogą zmieniać tylko operatorzy (OP). Aktualną wartość pokaże /donbass bosshp, poradnik – /donbasshelp."),
    "command.donbass.bosshp.error.empty": (
        "No multiplier given. Usage: /donbass bosshp <multiplier>, for example /donbass bosshp 1.5 (from %2$s to %3$s, decimal point).",
        "Множитель не указан. Синтаксис: /donbass bosshp <множитель>, например /donbass bosshp 1.5 (от %2$s до %3$s, дробная часть через точку).",
        "Nie podano mnożnika. Składnia: /donbass bosshp <mnożnik>, np. /donbass bosshp 1.5 (od %2$s do %3$s, część dziesiętna po kropce)."),
    "command.donbass.bosshp.error.format": (
        "\"%1$s\" is not a number. Usage: /donbass bosshp <multiplier>, for example /donbass bosshp 1.5 (from %2$s to %3$s, decimal point).",
        "«%1$s» — не число. Синтаксис: /donbass bosshp <множитель>, например /donbass bosshp 1.5 (от %2$s до %3$s, дробная часть через точку).",
        "„%1$s” to nie liczba. Składnia: /donbass bosshp <mnożnik>, np. /donbass bosshp 1.5 (od %2$s do %3$s, część dziesiętna po kropce)."),
    "command.donbass.bosshp.error.comma": (
        "Use a dot, not a comma: /donbass bosshp 1.5 (you typed \"%1$s\").",
        "Дробная часть пишется через точку, а не через запятую: /donbass bosshp 1.5 (вы ввели «%1$s»).",
        "Część dziesiętną zapisuje się po kropce, nie po przecinku: /donbass bosshp 1.5 (wpisano „%1$s”)."),
    "command.donbass.bosshp.error.negative": (
        "The multiplier must be positive (you typed \"%1$s\"). Usage: /donbass bosshp <multiplier>, from %2$s to %3$s.",
        "Множитель должен быть положительным (вы ввели «%1$s»). Синтаксис: /donbass bosshp <множитель>, от %2$s до %3$s.",
        "Mnożnik musi być dodatni (wpisano „%1$s”). Składnia: /donbass bosshp <mnożnik>, od %2$s do %3$s."),
    "command.donbass.bosshp.error.zero": (
        "The multiplier cannot be zero. Usage: /donbass bosshp <multiplier>, from %2$s to %3$s.",
        "Множитель не может быть нулевым. Синтаксис: /donbass bosshp <множитель>, от %2$s до %3$s.",
        "Mnożnik nie może być zerem. Składnia: /donbass bosshp <mnożnik>, od %2$s do %3$s."),
    "command.donbass.bosshp.error.min": (
        "\"%1$s\" is too small: the lowest multiplier is %2$s. Usage: /donbass bosshp <multiplier>, from %2$s to %3$s.",
        "«%1$s» — слишком мало: минимальный множитель %2$s. Синтаксис: /donbass bosshp <множитель>, от %2$s до %3$s.",
        "„%1$s” to za mało: najmniejszy mnożnik to %2$s. Składnia: /donbass bosshp <mnożnik>, od %2$s do %3$s."),
    "command.donbass.bosshp.error.max": (
        "\"%1$s\" is too large: the highest multiplier is %3$s (the game limits health to 1024). Usage: /donbass bosshp <multiplier>, from %2$s to %3$s.",
        "«%1$s» — слишком много: максимальный множитель %3$s (игра ограничивает здоровье значением 1024). Синтаксис: /donbass bosshp <множитель>, от %2$s до %3$s.",
        "„%1$s” to za dużo: największy mnożnik to %3$s (gra ogranicza zdrowie do 1024). Składnia: /donbass bosshp <mnożnik>, od %2$s do %3$s."),

    # ---- /donbasshelp: blocks (title + lines + examples); only what exists in the mod --------------------------
    "command.donbass.help.title": ("=== Donbass: guide ===", "=== Донбасс: справка ===", "=== Donbas: poradnik ==="),
    "command.donbass.help.footer": (
        "One block only: /donbasshelp factions | weapons | world | boss | bosshp | coop",
        "Только один блок: /donbasshelp factions | weapons | world | boss | bosshp | coop",
        "Tylko jeden blok: /donbasshelp factions | weapons | world | boss | bosshp | coop"),

    "command.donbass.help.factions.title": ("Factions and NPCs", "Фракции и NPC", "Frakcje i NPC"),
    "command.donbass.help.factions.1": (
        "Miners: peaceful traders; they sell for Miner's Tokens and offer more as their level grows. Hit one and it hits back, and its mates help.",
        "Шахтёры — мирные торговцы: продают за жетоны шахтёра, с ростом уровня ассортимент богаче. Ударите — ответит киркой, и соседи придут на помощь.",
        "Górnicy – pokojowi handlarze: sprzedają za żetony górnika, a im wyższy poziom, tym lepsza oferta. Uderzony oddaje kilofem, a koledzy pomagają."),
    "command.donbass.help.factions.2": (
        "DPR and LPR militiamen: hostile riflemen (recruit, fighter, sergeant) at checkpoints, plants, stations and deep mines.",
        "Ополченцы ДНР и ЛНР — враждебные стрелки (новобранец, боец, сержант): блокпосты, заводы, станции, глубокие шахты.",
        "Milicjanci DRL i ŁRL – wrogo nastawieni strzelcy (rekrut, bojownik, sierżant): posterunki, zakłady, stacje, głębokie kopalnie."),
    "command.donbass.help.factions.3": (
        "The two squads also shoot at each other (switch off in the config: factionsFight). They drop rounds, parts and pieces of their uniform.",
        "Два отряда стреляют и друг в друга (отключается в конфиге: factionsFight). Из них выпадают патроны, запчасти и части формы.",
        "Oba oddziały strzelają też do siebie (można wyłączyć w konfiguracji: factionsFight). Wypadają z nich naboje, części do broni i elementy munduru."),

    "command.donbass.help.weapons.title": ("Weapons and combat", "Оружие и бой", "Broń i walka"),
    "command.donbass.help.weapons.1": (
        "AK rifle: hold Use to fire, Shift + Use to reload (rounds come from your inventory). You shoot more accurately while sneaking.",
        "Автомат АК: удерживайте ПКМ — стрельба, Shift + ПКМ — перезарядка (патроны берутся из инвентаря). Приседая, стреляете точнее.",
        "Karabinek AK: przytrzymaj PPM – strzał, Shift + PPM – przeładowanie (naboje bierze z ekwipunku). Kucając, strzelasz celniej."),
    "command.donbass.help.weapons.2": (
        "Weapon Workbench: installs up to five AK modifications, one of each kind - magazine, reload, stabilizer, barrel, spring.",
        "Оружейный верстак: ставит до пяти модификаций АК, по одной каждого вида — магазин, перезарядка, стабилизатор, ствол, пружина.",
        "Warsztat zbrojeniowy: montuje do pięciu modyfikacji AK, po jednej z każdego rodzaju – magazynek, przeładowanie, stabilizator, lufa, sprężyna."),
    "command.donbass.help.weapons.3": (
        "Armour: miner's clothes and coal armour (full-set bonuses), DPR and LPR military uniforms.",
        "Броня: шахтёрская одежда и угольная броня (бонусы за полный комплект), военная форма ДНР и ЛНР.",
        "Pancerz: ubranie górnika i zbroja węglowa (premie za pełny komplet) oraz mundury wojskowe DRL i ŁRL."),

    "command.donbass.help.world.title": ("The world", "Мир", "Świat"),
    "command.donbass.help.world.1": (
        "Donbass Travel Voucher: Use it in the Overworld to go to the Donbass dimension, and there to come back.",
        "Путёвка в Донбасс: ПКМ в Верхнем мире — перенос в измерение «Донбасс», там же — обратно.",
        "Skierowanie do Donbasu: PPM w Overworldzie przenosi do wymiaru Donbas, a tam – z powrotem."),
    "command.donbass.help.world.2": (
        "Mines: shallow (hard hats and tools), active (miner's clothes, parts), deep (coal armour, weapon parts, a rare AK).",
        "Шахты: мелкие (каски и инструменты), действующие (шахтёрская одежда, запчасти), глубокие (угольная броня, запчасти, редкий АК).",
        "Kopalnie: płytkie (kaski i narzędzia), czynne (ubranie górnika, części), głębokie (zbroja węglowa, części do broni, rzadki AK)."),
    "command.donbass.help.world.3": (
        "Settlements, plants and freight stations: loot, miners and sometimes fighters. A rare Administration building holds the boss siren.",
        "Посёлки, заводы и грузовые станции: лут, шахтёры, иногда бойцы. В редком «Административном корпусе» лежит сирена босса.",
        "Osiedla, zakłady i stacje towarowe: łup, górnicy, czasem bojownicy. W rzadkim Budynku administracji leży syrena bossa."),
    "command.donbass.help.world.4": (
        "A checkpoint is held by one squad and flies its flag: DPR (black, blue, red) or LPR (light blue, blue, red). Its chests hold rounds, magazines and that squad's uniform.",
        "Блокпост охраняет один отряд, над ним развевается его флаг: ДНР (чёрный, синий, красный) или ЛНР (голубой, синий, красный). В сундуках — патроны, магазины и форма этого отряда.",
        "Posterunku strzeże jeden oddział, a nad nim powiewa jego flaga: DRL (czarna, niebieska, czerwona) lub ŁRL (błękitna, niebieska, czerwona). W skrzyniach są naboje, magazynki i mundur tego oddziału."),

    "command.donbass.help.boss.title": (
        "The boss: Chairman of the Coal Region", "Босс: Председатель Угольного края", "Boss: Przewodniczący Kraju Węglowego"),
    "command.donbass.help.boss.1": (
        "He never appears on his own. His siren calls him: Use it on open ground (it is used up). It does not work on Peaceful, or if another Chairman is within 160 blocks.",
        "Сам не появляется. Его вызывает сирена: ПКМ на открытом месте (расходуется). Не работает на мирной сложности и если рядом (160 блоков) уже есть другой Председатель.",
        "Sam się nie pojawia. Przywołuje go syrena: PPM na otwartym terenie (zużywa się). Nie działa na poziomie pokojowym ani gdy w promieniu 160 bloków stoi już inny Przewodniczący."),
    "command.donbass.help.boss.2": (
        "Siren: craft it (2 coal plates, bell, 2 rifle magazines, anthracite block, 2 weapon parts, diamond - plate, bell, plate / magazine, block, magazine / parts, diamond, parts) or find it in the Administration building.",
        "Сирена: скрафтите (2 угольные пластины, колокол, 2 магазина, блок антрацита, 2 оружейные запчасти, алмаз — пластина, колокол, пластина / магазин, блок, магазин / запчасти, алмаз, запчасти) или найдите в «Административном корпусе».",
        "Syrena: wytwórz ją (2 płyty węglowe, dzwon, 2 magazynki, blok antracytu, 2 części do broni, diament – płyta, dzwon, płyta / magazynek, blok, magazynek / części, diament, części) albo znajdź w Budynku administracji."),
    "command.donbass.help.boss.3": (
        "Three phases (below 66%% and 33%% of his health); he is invulnerable for about 3 seconds while changing phase. Bring armour, rounds and friends.",
        "Три фазы (ниже 66%% и 33%% здоровья); при смене фазы около 3 секунд неуязвим. Берите броню, патроны и друзей.",
        "Trzy fazy (poniżej 66%% i 33%% zdrowia); przy zmianie fazy przez ok. 3 sekundy jest nietykalny. Zabierz pancerz, naboje i przyjaciół."),
    "command.donbass.help.boss.4": (
        "Rewards: the Chairman's Pickaxe and Badge of Merit, tokens, diamonds, coal plates, rounds and parts.",
        "Награда: именная кирка и знак отличия Председателя, жетоны, алмазы, угольные пластины, патроны, запчасти.",
        "Nagroda: imienny kilof i odznaka zasługi Przewodniczącego, żetony, diamenty, płyty węglowe, naboje, części do broni."),

    "command.donbass.help.bosshp.title": ("Boss health: /donbass bosshp", "Здоровье босса: /donbass bosshp", "Zdrowie bossa: /donbass bosshp"),
    "command.donbass.help.bosshp.1": (
        "Sets the multiplier of the boss's maximum health (default 1.0). Only operators (OP) can change it; everybody can read it.",
        "Задаёт множитель максимального здоровья босса (по умолчанию 1.0). Менять могут только операторы (OP), смотреть — все.",
        "Ustawia mnożnik maksymalnego zdrowia bossa (domyślnie 1.0). Zmieniać mogą tylko operatorzy (OP), odczytać – wszyscy."),
    "command.donbass.help.bosshp.2": (
        "It applies to a boss summoned after the change; a boss that already stands keeps his health. Damage and behaviour do not change.",
        "Действует на босса, которого призовут после изменения; уже стоящий босс не меняется. Урон и поведение не меняются.",
        "Działa na bossa przywołanego po zmianie; boss, który już stoi, zachowuje zdrowie. Obrażenia i zachowanie się nie zmieniają."),
    "command.donbass.help.bosshp.3": (
        "Allowed: 0.1 to 3.2 with a decimal point (the game caps health at 1024); the value is saved with the world.",
        "Допустимо от 0.1 до 3.2, дробная часть через точку (игра ограничивает здоровье значением 1024); значение сохраняется вместе с миром.",
        "Dozwolone od 0.1 do 3.2, część dziesiętna po kropce (gra ogranicza zdrowie do 1024); wartość jest zapisywana ze światem."),
    "command.donbass.help.bosshp.ex1": (
        "/donbass bosshp - show the current value", "/donbass bosshp — показать текущий множитель",
        "/donbass bosshp – pokaż bieżącą wartość"),
    "command.donbass.help.bosshp.ex2": (
        "/donbass bosshp 2 - twice the health", "/donbass bosshp 2 — вдвое больше здоровья",
        "/donbass bosshp 2 – dwa razy więcej zdrowia"),
    "command.donbass.help.bosshp.ex3": (
        "/donbass bosshp 1.5 - one and a half times", "/donbass bosshp 1.5 — в полтора раза больше",
        "/donbass bosshp 1.5 – półtora raza więcej"),
    "command.donbass.help.bosshp.ex4": (
        "/donbass bosshp 3 - three times the health", "/donbass bosshp 3 — втрое больше здоровья",
        "/donbass bosshp 3 – trzy razy więcej zdrowia"),
    "command.donbass.help.bosshp.ex5": (
        "/donbass bosshp 0.75 - 75%% of the standard health", "/donbass bosshp 0.75 — 75%% стандартного здоровья",
        "/donbass bosshp 0.75 – 75%% standardowego zdrowia"),

    "command.donbass.help.coop.title": (
        "Co-op: recommended boss health", "Кооператив: рекомендуемое здоровье босса", "Kooperacja: zalecane zdrowie bossa"),
    "command.donbass.help.coop.1": ("1 player: x1.0", "1 игрок: ×1.0", "1 gracz: ×1.0"),
    "command.donbass.help.coop.2": ("2 players: x1.5", "2 игрока: ×1.5", "2 graczy: ×1.5"),
    "command.donbass.help.coop.3": ("3 players: x2.0", "3 игрока: ×2.0", "3 graczy: ×2.0"),
    "command.donbass.help.coop.4": ("4 players: x2.5", "4 игрока: ×2.5", "4 graczy: ×2.5"),
    "command.donbass.help.coop.5": ("5-6 players: x3.0", "5–6 игроков: ×3.0", "5–6 graczy: ×3.0"),
    "command.donbass.help.coop.6": (
        "These are approximate values: change them to suit your gear and the damage your group deals. Set them with /donbass bosshp before summoning the boss.",
        "Значения ориентировочные: меняйте их под вашу экипировку и урон отряда. Задайте командой /donbass bosshp до призыва босса.",
        "To wartości orientacyjne: zmieniaj je zależnie od ekwipunku i obrażeń zadawanych przez grupę. Ustaw je komendą /donbass bosshp przed przywołaniem bossa."),
})

package com.donbass.mod.config;

import net.minecraftforge.common.ForgeConfigSpec;

/**
 * Common config (config/donbass-common.toml). Every accessor falls back to the default while the
 * config is not loaded yet (tooltips and the creative tab are built early on the client).
 */
public final class DonbassConfig {
    public static final ForgeConfigSpec SPEC;

    private static final ForgeConfigSpec.DoubleValue MINER_SPAWN_CHANCE;
    private static final ForgeConfigSpec.DoubleValue FIGHTER_SPAWN_CHANCE;
    private static final ForgeConfigSpec.BooleanValue FACTIONS_FIGHT;
    private static final ForgeConfigSpec.DoubleValue FIGHTER_DAMAGE_MULTIPLIER;
    private static final ForgeConfigSpec.IntValue MINER_RESTOCK_TICKS;
    private static final ForgeConfigSpec.DoubleValue RIFLE_DAMAGE;
    private static final ForgeConfigSpec.IntValue RIFLE_FIRE_INTERVAL;
    private static final ForgeConfigSpec.IntValue RIFLE_MAGAZINE;
    private static final ForgeConfigSpec.IntValue RIFLE_RELOAD_TICKS;
    private static final ForgeConfigSpec.DoubleValue RIFLE_SPREAD;
    private static final ForgeConfigSpec.BooleanValue ARMOR_SET_BONUSES;
    private static final ForgeConfigSpec.DoubleValue BOSS_HEALTH;
    private static final ForgeConfigSpec.DoubleValue BOSS_DAMAGE_MULTIPLIER;

    static {
        ForgeConfigSpec.Builder b = new ForgeConfigSpec.Builder();

        b.comment("Natural spawning inside structures (mines, settlements, plants, checkpoints).",
                "Mobs that are part of a structure when it is generated are not affected.").push("spawning");
        MINER_SPAWN_CHANCE = b.comment("Chance (0..1) that a natural spawn attempt of a miner succeeds. 0 disables natural miner spawns.")
                .defineInRange("minerSpawnChance", 0.5D, 0.0D, 1.0D);
        FIGHTER_SPAWN_CHANCE = b.comment("Chance (0..1) that a natural spawn attempt of a militiaman (DPR / LPR) succeeds. 0 disables natural fighter spawns.")
                .defineInRange("fighterSpawnChance", 0.5D, 0.0D, 1.0D);
        b.pop();

        b.push("fighters");
        FACTIONS_FIGHT = b.comment("DPR and LPR militiamen attack each other on sight (set false to make them ignore each other).")
                .define("factionsFight", true);
        FIGHTER_DAMAGE_MULTIPLIER = b.comment("Multiplier for the damage of fighter bullets (1.0 = default).")
                .defineInRange("fighterDamageMultiplier", 1.0D, 0.0D, 10.0D);
        b.pop();

        b.push("miners");
        MINER_RESTOCK_TICKS = b.comment("Ticks between trade restocks of a miner (6000 = 5 minutes).")
                .defineInRange("minerRestockTicks", 6000, 200, 1_000_000);
        b.pop();

        b.push("rifle");
        RIFLE_DAMAGE = b.comment("Damage of one bullet of the player's AK (2.0 = one heart).")
                .defineInRange("damage", 5.0D, 0.0D, 100.0D);
        RIFLE_FIRE_INTERVAL = b.comment("Ticks between two shots while the trigger is held (20 ticks = 1 second).")
                .defineInRange("fireIntervalTicks", 3, 1, 40);
        RIFLE_MAGAZINE = b.comment("Rounds in a full magazine.")
                .defineInRange("magazineSize", 30, 1, 200);
        RIFLE_RELOAD_TICKS = b.comment("Ticks needed to reload.")
                .defineInRange("reloadTicks", 45, 5, 400);
        RIFLE_SPREAD = b.comment("Bullet spread in degrees (random cone; halved while sneaking).")
                .defineInRange("spreadDegrees", 1.6D, 0.0D, 30.0D);
        b.pop();

        b.push("armor");
        ARMOR_SET_BONUSES = b.comment("Enable the full-set bonuses of the coal armour and the miner's clothes.")
                .define("setBonuses", true);
        b.pop();

        b.comment("The Combine Director (boss). It never spawns by itself: only the Combine Siren calls it.").push("boss");
        BOSS_HEALTH = b.comment("Maximum health of the boss (applied when it is summoned).")
                .defineInRange("health", 320.0D, 40.0D, 5000.0D);
        BOSS_DAMAGE_MULTIPLIER = b.comment("Multiplier for all damage dealt by the boss (1.0 = default).")
                .defineInRange("damageMultiplier", 1.0D, 0.0D, 10.0D);
        b.pop();

        SPEC = b.build();
    }

    private DonbassConfig() {}

    public static double minerSpawnChance() {
        return SPEC.isLoaded() ? MINER_SPAWN_CHANCE.get() : 0.5D;
    }

    public static double fighterSpawnChance() {
        return SPEC.isLoaded() ? FIGHTER_SPAWN_CHANCE.get() : 0.5D;
    }

    public static boolean factionsFight() {
        return !SPEC.isLoaded() || FACTIONS_FIGHT.get();
    }

    public static double fighterDamageMultiplier() {
        return SPEC.isLoaded() ? FIGHTER_DAMAGE_MULTIPLIER.get() : 1.0D;
    }

    public static int minerRestockTicks() {
        return SPEC.isLoaded() ? MINER_RESTOCK_TICKS.get() : 6000;
    }

    public static float rifleDamage() {
        return SPEC.isLoaded() ? RIFLE_DAMAGE.get().floatValue() : 5.0F;
    }

    public static int rifleFireInterval() {
        return SPEC.isLoaded() ? RIFLE_FIRE_INTERVAL.get() : 3;
    }

    public static int rifleMagazine() {
        return SPEC.isLoaded() ? RIFLE_MAGAZINE.get() : 30;
    }

    public static int rifleReloadTicks() {
        return SPEC.isLoaded() ? RIFLE_RELOAD_TICKS.get() : 45;
    }

    public static double rifleSpread() {
        return SPEC.isLoaded() ? RIFLE_SPREAD.get() : 1.6D;
    }

    public static double bossHealth() {
        return SPEC.isLoaded() ? BOSS_HEALTH.get() : 320.0D;
    }

    public static double bossDamageMultiplier() {
        return SPEC.isLoaded() ? BOSS_DAMAGE_MULTIPLIER.get() : 1.0D;
    }

    public static boolean armorSetBonuses() {
        return !SPEC.isLoaded() || ARMOR_SET_BONUSES.get();
    }
}

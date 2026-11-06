package com.donbass.mod.boss;

import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.Tag;
import net.minecraft.server.MinecraftServer;
import net.minecraft.world.level.saveddata.SavedData;

/**
 * World-wide boss settings (0.4.0): today only the health multiplier set with {@code /donbass bosshp}. Stored with
 * the world (the overworld's data storage, file data/donbass_boss_settings.dat), so it survives restarts and is the
 * same for every player and every dimension; it is read and written on the server thread only.
 *
 * <p>The multiplier is read once, when a boss is set up ({@code CombineDirectorEntity.setUp}); a boss that already
 * stands in the world keeps the health it was created with.
 */
public final class BossSettings extends SavedData {
    public static final String DATA_NAME = "donbass_boss_settings";
    private static final String TAG_HEALTH_MULTIPLIER = "HealthMultiplier";

    private double healthMultiplier = BossMultiplier.DEFAULT;

    public BossSettings() {}

    public static BossSettings get(MinecraftServer server) {
        return server.overworld().getDataStorage().computeIfAbsent(BossSettings::load, BossSettings::new, DATA_NAME);
    }

    public static BossSettings load(CompoundTag tag) {
        BossSettings settings = new BossSettings();
        if (tag.contains(TAG_HEALTH_MULTIPLIER, Tag.TAG_DOUBLE)) {
            settings.healthMultiplier = BossMultiplier.sanitize(tag.getDouble(TAG_HEALTH_MULTIPLIER));
        }
        return settings;
    }

    @Override
    public CompoundTag save(CompoundTag tag) {
        tag.putDouble(TAG_HEALTH_MULTIPLIER, healthMultiplier);
        return tag;
    }

    public double healthMultiplier() {
        return healthMultiplier;
    }

    public void setHealthMultiplier(double multiplier) {
        this.healthMultiplier = BossMultiplier.sanitize(multiplier);
        setDirty();
    }
}

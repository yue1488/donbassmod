package com.donbass.mod.worldgen;

import com.donbass.mod.DonbassMod;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.level.Level;

/** Key of the data-driven Donbass dimension (data/donbass/dimension/donbass.json). */
public final class DonbassDimension {
    public static final ResourceKey<Level> KEY =
            ResourceKey.create(Registries.DIMENSION, new ResourceLocation(DonbassMod.MOD_ID, "donbass"));

    private DonbassDimension() {}
}

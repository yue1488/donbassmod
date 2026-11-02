package com.donbass.mod.registry;

import com.donbass.mod.DonbassMod;
import com.donbass.mod.worldgen.CoalSeamFeature;
import com.donbass.mod.worldgen.TerriconeFeature;
import net.minecraft.world.level.levelgen.feature.Feature;
import net.minecraft.world.level.levelgen.feature.configurations.NoneFeatureConfiguration;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

public final class ModFeatures {
    public static final DeferredRegister<Feature<?>> FEATURES =
            DeferredRegister.create(ForgeRegistries.FEATURES, DonbassMod.MOD_ID);

    public static final RegistryObject<Feature<NoneFeatureConfiguration>> COAL_SEAM =
            FEATURES.register("coal_seam", () -> new CoalSeamFeature(NoneFeatureConfiguration.CODEC));

    public static final RegistryObject<Feature<NoneFeatureConfiguration>> TERRICONE =
            FEATURES.register("terricone", () -> new TerriconeFeature(NoneFeatureConfiguration.CODEC));

    private ModFeatures() {}
}

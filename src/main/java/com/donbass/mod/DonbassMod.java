package com.donbass.mod;

import com.donbass.mod.config.DonbassConfig;
import com.donbass.mod.registry.ModBlocks;
import com.donbass.mod.registry.ModCreativeTabs;
import com.donbass.mod.registry.ModEntities;
import com.donbass.mod.registry.ModFeatures;
import com.donbass.mod.registry.ModItems;
import com.donbass.mod.registry.ModSounds;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.fml.ModLoadingContext;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.config.ModConfig;
import net.minecraftforge.fml.javafmlmod.FMLJavaModLoadingContext;

@Mod(DonbassMod.MOD_ID)
public class DonbassMod {
    public static final String MOD_ID = "donbass";

    public DonbassMod() {
        IEventBus modBus = FMLJavaModLoadingContext.get().getModEventBus();

        // Blocks first: ModBlocks also queues the matching BlockItems into ModItems.ITEMS.
        ModBlocks.BLOCKS.register(modBus);
        ModItems.ITEMS.register(modBus);
        ModSounds.SOUNDS.register(modBus);
        ModEntities.ENTITIES.register(modBus);
        ModFeatures.FEATURES.register(modBus);
        ModCreativeTabs.TABS.register(modBus);

        ModLoadingContext.get().registerConfig(ModConfig.Type.COMMON, DonbassConfig.SPEC);
    }
}

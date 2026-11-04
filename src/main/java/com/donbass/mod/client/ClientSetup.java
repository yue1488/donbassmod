package com.donbass.mod.client;

import com.donbass.mod.DonbassMod;
import com.donbass.mod.registry.ModEntities;
import com.donbass.mod.registry.ModMenus;
import net.minecraft.client.gui.screens.MenuScreens;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.client.event.EntityRenderersEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.event.lifecycle.FMLClientSetupEvent;

@Mod.EventBusSubscriber(modid = DonbassMod.MOD_ID, bus = Mod.EventBusSubscriber.Bus.MOD, value = Dist.CLIENT)
public final class ClientSetup {
    private ClientSetup() {}

    @SubscribeEvent
    public static void registerRenderers(EntityRenderersEvent.RegisterRenderers event) {
        event.registerEntityRenderer(ModEntities.MINER.get(), MinerRenderer::new);
        event.registerEntityRenderer(ModEntities.NORTH_FIGHTER.get(), context -> new MilitiaRenderer(context, "north_fighter"));
        event.registerEntityRenderer(ModEntities.SOUTH_FIGHTER.get(), context -> new MilitiaRenderer(context, "south_fighter"));
        event.registerEntityRenderer(ModEntities.COMBINE_DIRECTOR.get(), DirectorRenderer::new);
    }

    @SubscribeEvent
    public static void clientSetup(FMLClientSetupEvent event) {
        event.enqueueWork(() -> MenuScreens.register(ModMenus.WORKBENCH.get(), WorkbenchScreen::new));
    }
}

package com.donbass.mod.event;

import com.donbass.mod.DonbassMod;
import com.donbass.mod.registry.ModBlocks;
import net.minecraft.world.item.Item;
import net.minecraftforge.event.furnace.FurnaceFuelBurnTimeEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

/**
 * Burn times for the fuel blocks (items such as anthracite and coke carry their own burn time).
 * Vanilla: coal = 1600 ticks, coal block = 16000 ticks.
 */
@Mod.EventBusSubscriber(modid = DonbassMod.MOD_ID, bus = Mod.EventBusSubscriber.Bus.FORGE)
public final class FuelHandler {
    private FuelHandler() {}

    @SubscribeEvent
    public static void onFuelBurnTime(FurnaceFuelBurnTimeEvent event) {
        Item item = event.getItemStack().getItem();
        if (item == ModBlocks.ANTHRACITE_BLOCK.get().asItem()) {
            event.setBurnTime(28800); // 9 x 3200
        } else if (item == ModBlocks.COKE_BLOCK.get().asItem()) {
            event.setBurnTime(21600); // 9 x 2400
        }
    }
}

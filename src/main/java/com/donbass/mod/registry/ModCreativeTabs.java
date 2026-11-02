package com.donbass.mod.registry;

import com.donbass.mod.DonbassMod;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.RegistryObject;

public final class ModCreativeTabs {
    public static final DeferredRegister<CreativeModeTab> TABS =
            DeferredRegister.create(Registries.CREATIVE_MODE_TAB, DonbassMod.MOD_ID);

    public static final RegistryObject<CreativeModeTab> DONBASS_TAB = TABS.register("donbass",
            () -> CreativeModeTab.builder()
                    .title(Component.translatable("itemGroup.donbass"))
                    .icon(() -> new ItemStack(ModItems.ANTHRACITE.get()))
                    .displayItems((parameters, output) ->
                            ModItems.ITEMS.getEntries().forEach(entry -> output.accept(entry.get())))
                    .build());

    private ModCreativeTabs() {}
}

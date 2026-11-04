package com.donbass.mod.registry;

import com.donbass.mod.DonbassMod;
import com.donbass.mod.menu.WorkbenchMenu;
import net.minecraft.world.inventory.MenuType;
import net.minecraftforge.common.extensions.IForgeMenuType;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

public final class ModMenus {
    public static final DeferredRegister<MenuType<?>> MENUS =
            DeferredRegister.create(ForgeRegistries.MENU_TYPES, DonbassMod.MOD_ID);

    public static final RegistryObject<MenuType<WorkbenchMenu>> WORKBENCH = MENUS.register("weapon_workbench",
            () -> IForgeMenuType.create((windowId, inventory, buf) -> new WorkbenchMenu(windowId, inventory)));

    private ModMenus() {}
}

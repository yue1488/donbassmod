package com.donbass.mod.item;

import java.util.List;
import javax.annotation.Nullable;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.Level;

/** A modification kit for the AK. It does nothing by itself: it is installed at the Weapon Workbench. */
public class AkModItem extends Item {
    private final AkMods.Mod mod;

    public AkModItem(Item.Properties properties, AkMods.Mod mod) {
        super(properties);
        this.mod = mod;
    }

    public AkMods.Mod mod() {
        return mod;
    }

    @Override
    public void appendHoverText(ItemStack stack, @Nullable Level level, List<Component> tooltip, TooltipFlag flag) {
        tooltip.add(Component.translatable(mod.effectKey()).withStyle(ChatFormatting.GREEN));
        tooltip.add(Component.translatable("tooltip.donbass.ak_mod_install").withStyle(ChatFormatting.DARK_GRAY));
    }
}

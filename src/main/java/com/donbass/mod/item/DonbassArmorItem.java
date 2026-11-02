package com.donbass.mod.item;

import com.donbass.mod.registry.ModArmorMaterials;
import java.util.List;
import javax.annotation.Nullable;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.ArmorItem;
import net.minecraft.world.item.ArmorMaterial;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.Level;

/** Armour piece of one of the four Donbass sets; adds the set description to the tooltip. */
public class DonbassArmorItem extends ArmorItem {
    public DonbassArmorItem(ArmorMaterial material, ArmorItem.Type type, Item.Properties properties) {
        super(material, type, properties);
    }

    @Override
    public void appendHoverText(ItemStack stack, @Nullable Level level, List<Component> tooltip, TooltipFlag flag) {
        ArmorMaterial material = getMaterial();
        if (material == ModArmorMaterials.COAL) {
            tooltip.add(Component.translatable("tooltip.donbass.set_coal").withStyle(ChatFormatting.GOLD));
        } else if (material == ModArmorMaterials.MINERS) {
            tooltip.add(Component.translatable("tooltip.donbass.set_miners").withStyle(ChatFormatting.GOLD));
        } else {
            tooltip.add(Component.translatable("tooltip.donbass.set_field").withStyle(ChatFormatting.GRAY));
        }
    }
}

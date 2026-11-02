package com.donbass.mod.item;

import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.RecipeType;

/** A plain item that can be burned in furnaces for a fixed number of ticks. */
public class FuelItem extends Item {
    private final int burnTime;

    public FuelItem(int burnTime, Item.Properties properties) {
        super(properties);
        this.burnTime = burnTime;
    }

    @Override
    public int getBurnTime(ItemStack itemStack, RecipeType<?> recipeType) {
        return burnTime;
    }
}

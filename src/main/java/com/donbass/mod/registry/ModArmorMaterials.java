package com.donbass.mod.registry;

import com.donbass.mod.DonbassMod;
import java.util.function.Supplier;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.item.ArmorItem;
import net.minecraft.world.item.ArmorMaterial;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.crafting.Ingredient;

/**
 * Armour materials. The name is "donbass:<id>", so the layer textures are
 * assets/donbass/textures/models/armor/<id>_layer_1.png and _layer_2.png (see tools/gen_textures_gear.py).
 * Defence values are listed as helmet, chestplate, leggings, boots.
 */
public enum ModArmorMaterials implements ArmorMaterial {
    // work clothes: leather-like, cheap and early (total defence 8)
    MINERS("miners", 12, new int[] {2, 3, 2, 1}, 10, SoundEvents.ARMOR_EQUIP_LEATHER, 0.0F, 0.0F,
            () -> Ingredient.of(Items.LEATHER)),
    // iron-class protection (15) with a little extra toughness; the set bonus is in ArmorBonusHandler
    COAL("coal", 22, new int[] {2, 6, 5, 2}, 9, SoundEvents.ARMOR_EQUIP_IRON, 0.5F, 0.0F,
            () -> Ingredient.of(ModItems.COAL_PLATE.get())),
    // field uniforms: between leather and iron (12 and 13)
    STEPPE("steppe", 14, new int[] {2, 5, 4, 1}, 9, SoundEvents.ARMOR_EQUIP_CHAIN, 0.0F, 0.0F,
            () -> Ingredient.of(Items.LEATHER)),
    TERRICONE("terricone", 16, new int[] {2, 5, 4, 2}, 9, SoundEvents.ARMOR_EQUIP_CHAIN, 0.0F, 0.02F,
            () -> Ingredient.of(Items.LEATHER));

    /** Vanilla base durabilities per slot: helmet 11, chestplate 16, leggings 15, boots 13. */
    private static final int[] BASE_DURABILITY = {11, 16, 15, 13};

    private final String name;
    private final int durabilityMultiplier;
    private final int[] defense;
    private final int enchantability;
    private final SoundEvent equipSound;
    private final float toughness;
    private final float knockbackResistance;
    private final Supplier<Ingredient> repair;
    private Ingredient repairCache;

    ModArmorMaterials(String name, int durabilityMultiplier, int[] defense, int enchantability, SoundEvent equipSound,
                      float toughness, float knockbackResistance, Supplier<Ingredient> repair) {
        this.name = DonbassMod.MOD_ID + ":" + name;
        this.durabilityMultiplier = durabilityMultiplier;
        this.defense = defense;
        this.enchantability = enchantability;
        this.equipSound = equipSound;
        this.toughness = toughness;
        this.knockbackResistance = knockbackResistance;
        this.repair = repair;
    }

    private static int index(ArmorItem.Type type) {
        return switch (type) {
            case HELMET -> 0;
            case CHESTPLATE -> 1;
            case LEGGINGS -> 2;
            case BOOTS -> 3;
        };
    }

    @Override
    public int getDurabilityForType(ArmorItem.Type type) {
        return BASE_DURABILITY[index(type)] * durabilityMultiplier;
    }

    @Override
    public int getDefenseForType(ArmorItem.Type type) {
        return defense[index(type)];
    }

    @Override
    public int getEnchantmentValue() {
        return enchantability;
    }

    @Override
    public SoundEvent getEquipSound() {
        return equipSound;
    }

    @Override
    public Ingredient getRepairIngredient() {
        if (repairCache == null) {
            repairCache = repair.get();
        }
        return repairCache;
    }

    @Override
    public String getName() {
        return name;
    }

    @Override
    public float getToughness() {
        return toughness;
    }

    @Override
    public float getKnockbackResistance() {
        return knockbackResistance;
    }
}

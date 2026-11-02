package com.donbass.mod.event;

import com.donbass.mod.DonbassMod;
import com.donbass.mod.config.DonbassConfig;
import com.donbass.mod.registry.ModArmorMaterials;
import com.donbass.mod.registry.ModSounds;
import net.minecraft.network.chat.Component;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ArmorItem;
import net.minecraft.world.item.ArmorMaterial;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.event.entity.living.LivingHurtEvent;
import net.minecraftforge.event.entity.player.PlayerEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

/**
 * Full-set bonuses.
 * Coal armour: permanent fire resistance (also against lava and smouldering spoil) and 25% less explosion damage.
 * Miner's clothes: 20% faster mining while there is rock above the head.
 */
@Mod.EventBusSubscriber(modid = DonbassMod.MOD_ID, bus = Mod.EventBusSubscriber.Bus.FORGE)
public final class ArmorBonusHandler {
    private static final EquipmentSlot[] ARMOR_SLOTS =
            {EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.LEGS, EquipmentSlot.FEET};

    private ArmorBonusHandler() {}

    public static boolean wearsFullSet(LivingEntity entity, ArmorMaterial material) {
        for (EquipmentSlot slot : ARMOR_SLOTS) {
            ItemStack stack = entity.getItemBySlot(slot);
            if (!(stack.getItem() instanceof ArmorItem armor) || armor.getMaterial() != material) {
                return false;
            }
        }
        return true;
    }

    @SubscribeEvent
    public static void onPlayerTick(TickEvent.PlayerTickEvent event) {
        if (event.phase != TickEvent.Phase.END || event.player.level().isClientSide()) {
            return;
        }
        Player player = event.player;
        if (player.tickCount % 40 != 0 || !DonbassConfig.armorSetBonuses()) {
            return;
        }
        if (wearsFullSet(player, ModArmorMaterials.COAL)) {
            if (!player.hasEffect(MobEffects.FIRE_RESISTANCE)) {
                player.level().playSound(null, player.blockPosition(), ModSounds.COAL_SET.get(), SoundSource.PLAYERS,
                        0.6F, 1.0F);
                player.displayClientMessage(Component.translatable("message.donbass.coal_set_on"), true);
            }
            // ambient, no particles, with an icon: renewed before it runs out
            player.addEffect(new MobEffectInstance(MobEffects.FIRE_RESISTANCE, 100, 0, true, false, true));
        }
    }

    @SubscribeEvent
    public static void onBreakSpeed(PlayerEvent.BreakSpeed event) {
        Player player = event.getEntity();
        if (!DonbassConfig.armorSetBonuses() || !wearsFullSet(player, ModArmorMaterials.MINERS)) {
            return;
        }
        if (!player.level().canSeeSky(player.blockPosition())) {
            event.setNewSpeed(event.getNewSpeed() * 1.2F);
        }
    }

    @SubscribeEvent
    public static void onHurt(LivingHurtEvent event) {
        LivingEntity entity = event.getEntity();
        if (DonbassConfig.armorSetBonuses() && event.getSource().is(DamageTypeTags.IS_EXPLOSION)
                && wearsFullSet(entity, ModArmorMaterials.COAL)) {
            event.setAmount(event.getAmount() * 0.75F);
        }
    }
}

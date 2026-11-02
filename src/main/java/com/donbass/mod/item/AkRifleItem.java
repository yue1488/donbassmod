package com.donbass.mod.item;

import com.donbass.mod.client.AkClientExtensions;
import com.donbass.mod.client.ClientHooks;
import com.donbass.mod.combat.Ballistics;
import com.donbass.mod.config.DonbassConfig;
import com.donbass.mod.registry.ModItems;
import com.donbass.mod.registry.ModSounds;
import java.util.List;
import java.util.function.Consumer;
import javax.annotation.Nullable;
import net.minecraft.ChatFormatting;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.UseAnim;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.client.extensions.common.IClientItemExtensions;
import net.minecraftforge.fml.DistExecutor;

/**
 * The AK assault rifle. Hold Use to fire (full auto), Shift + Use to reload.
 * The magazine content lives in the stack NBT ("Ammo"); a reload in progress is stored as the game time it
 * ends at ("ReloadEnd"). Rounds are taken from the player's inventory (donbass:rifle_cartridge).
 */
public class AkRifleItem extends Item {
    public static final String TAG_AMMO = "Ammo";
    public static final String TAG_RELOAD_END = "ReloadEnd";
    private static final double RANGE = 64.0D;

    public AkRifleItem(Item.Properties properties) {
        super(properties);
    }

    // ------------------------------------------------------------ state ----
    public static int getAmmo(ItemStack stack) {
        CompoundTag tag = stack.getTag();
        return tag == null ? 0 : tag.getInt(TAG_AMMO);
    }

    public static void setAmmo(ItemStack stack, int ammo) {
        stack.getOrCreateTag().putInt(TAG_AMMO, Math.max(0, ammo));
    }

    public static boolean isReloading(ItemStack stack) {
        CompoundTag tag = stack.getTag();
        return tag != null && tag.contains(TAG_RELOAD_END);
    }

    public static long getReloadEnd(ItemStack stack) {
        CompoundTag tag = stack.getTag();
        return tag == null ? 0L : tag.getLong(TAG_RELOAD_END);
    }

    private static int countCartridges(Player player) {
        int total = 0;
        Inventory inv = player.getInventory();
        for (ItemStack s : inv.items) {
            if (s.is(ModItems.RIFLE_CARTRIDGE.get())) {
                total += s.getCount();
            }
        }
        for (ItemStack s : inv.offhand) {
            if (s.is(ModItems.RIFLE_CARTRIDGE.get())) {
                total += s.getCount();
            }
        }
        return total;
    }

    /** Removes up to 'wanted' cartridges from the inventory, returns how many were taken. */
    private static int takeCartridges(Player player, int wanted) {
        int taken = 0;
        Inventory inv = player.getInventory();
        for (ItemStack s : inv.items) {
            if (taken >= wanted) {
                break;
            }
            if (s.is(ModItems.RIFLE_CARTRIDGE.get())) {
                int n = Math.min(s.getCount(), wanted - taken);
                s.shrink(n);
                taken += n;
            }
        }
        for (ItemStack s : inv.offhand) {
            if (taken >= wanted) {
                break;
            }
            if (s.is(ModItems.RIFLE_CARTRIDGE.get())) {
                int n = Math.min(s.getCount(), wanted - taken);
                s.shrink(n);
                taken += n;
            }
        }
        inv.setChanged();
        return taken;
    }

    // ------------------------------------------------------------- use ----
    @Override
    public UseAnim getUseAnimation(ItemStack stack) {
        return UseAnim.NONE;
    }

    @Override
    public int getUseDuration(ItemStack stack) {
        return 72000;
    }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (isReloading(stack)) {
            return InteractionResultHolder.fail(stack);
        }
        if (player.isShiftKeyDown()) {
            if (!level.isClientSide) {
                startReload(level, player, stack, true);
            }
            return InteractionResultHolder.sidedSuccess(stack, level.isClientSide());
        }
        player.startUsingItem(hand);
        return InteractionResultHolder.consume(stack);
    }

    @Override
    public void onUseTick(Level level, LivingEntity entity, ItemStack stack, int remainingUseDuration) {
        if (!(entity instanceof Player player)) {
            return;
        }
        int interval = DonbassConfig.rifleFireInterval();
        int used = getUseDuration(stack) - remainingUseDuration;
        if (used % interval != 0 || isReloading(stack)) {
            return;
        }
        boolean creative = player.getAbilities().instabuild;
        if (getAmmo(stack) <= 0 && !creative) {
            if (!level.isClientSide) {
                if (used == 0) {
                    level.playSound(null, player.getX(), player.getY(), player.getZ(), ModSounds.AK_EMPTY.get(),
                            SoundSource.PLAYERS, 0.8F, 1.0F);
                }
                startReload(level, player, stack, false);
            }
            return;
        }
        if (level.isClientSide) {
            DistExecutor.unsafeRunWhenOn(Dist.CLIENT, () -> () -> ClientHooks.onRifleShot(player));
            return;
        }
        fire(level, player, stack, creative);
    }

    private void fire(Level level, Player player, ItemStack stack, boolean creative) {
        if (!creative) {
            setAmmo(stack, getAmmo(stack) - 1);
        }
        double spread = DonbassConfig.rifleSpread() * (player.isShiftKeyDown() ? 0.5D : 1.0D);
        if (player.getDeltaMovement().horizontalDistanceSqr() > 0.01D) {
            spread *= 1.6D;
        }
        Vec3 eye = player.getEyePosition();
        Vec3 dir = Ballistics.spread(level.random, player.getLookAngle(), spread);
        Ballistics.shoot(level, player, eye, dir, RANGE, DonbassConfig.rifleDamage(), Ballistics.defaultFilter(player));

        level.playSound(null, player.getX(), player.getY(), player.getZ(), ModSounds.AK_SHOT.get(),
                SoundSource.PLAYERS, 1.2F, 0.95F + level.random.nextFloat() * 0.1F);
        if (level instanceof ServerLevel server) {
            Vec3 muzzle = eye.add(dir.scale(1.1D)).add(0.0D, -0.12D, 0.0D);
            server.sendParticles(ParticleTypes.SMOKE, muzzle.x, muzzle.y, muzzle.z, 2, 0.03D, 0.03D, 0.03D, 0.0D);
            server.sendParticles(ParticleTypes.FLAME, muzzle.x, muzzle.y, muzzle.z, 1, 0.0D, 0.0D, 0.0D, 0.0D);
        }
        if (getAmmo(stack) <= 0 && !creative) {
            player.displayClientMessage(Component.translatable("message.donbass.rifle_empty_mag"), true);
        }
    }

    // ----------------------------------------------------------- reload ----
    public static void startReload(Level level, Player player, ItemStack stack, boolean manual) {
        int max = DonbassConfig.rifleMagazine();
        boolean creative = player.getAbilities().instabuild;
        if (getAmmo(stack) >= max) {
            if (manual) {
                player.displayClientMessage(Component.translatable("message.donbass.rifle_full"), true);
            }
            return;
        }
        if (!creative && countCartridges(player) <= 0) {
            player.displayClientMessage(Component.translatable("message.donbass.rifle_no_ammo"), true);
            return;
        }
        stack.getOrCreateTag().putLong(TAG_RELOAD_END, level.getGameTime() + DonbassConfig.rifleReloadTicks());
        level.playSound(null, player.getX(), player.getY(), player.getZ(), ModSounds.AK_RELOAD.get(),
                SoundSource.PLAYERS, 0.9F, 1.0F);
    }

    private static void finishReload(Player player, ItemStack stack) {
        int max = DonbassConfig.rifleMagazine();
        int missing = Math.max(0, max - getAmmo(stack));
        int loaded = player.getAbilities().instabuild ? missing : takeCartridges(player, missing);
        setAmmo(stack, getAmmo(stack) + loaded);
        CompoundTag tag = stack.getTag();
        if (tag != null) {
            tag.remove(TAG_RELOAD_END);
        }
        if (loaded == 0) {
            player.displayClientMessage(Component.translatable("message.donbass.rifle_no_ammo"), true);
        }
    }

    @Override
    public void inventoryTick(ItemStack stack, Level level, Entity entity, int slot, boolean selected) {
        if (level.isClientSide || !isReloading(stack) || !(entity instanceof Player player)) {
            return;
        }
        boolean inHand = selected || player.getOffhandItem() == stack;
        if (!inHand) {                       // put away during a reload: cancel it
            CompoundTag tag = stack.getTag();
            if (tag != null) {
                tag.remove(TAG_RELOAD_END);
            }
            return;
        }
        if (level.getGameTime() >= getReloadEnd(stack)) {
            finishReload(player, stack);
        }
    }

    /** The magazine counter changes the NBT all the time: do not replay the equip animation for that. */
    @Override
    public boolean shouldCauseReequipAnimation(ItemStack oldStack, ItemStack newStack, boolean slotChanged) {
        return slotChanged || !oldStack.is(newStack.getItem());
    }

    @Override
    public boolean shouldCauseBlockBreakReset(ItemStack oldStack, ItemStack newStack) {
        return !oldStack.is(newStack.getItem());
    }

    // ----------------------------------------------------------- client ----
    @Override
    public void appendHoverText(ItemStack stack, @Nullable Level level, List<Component> tooltip, TooltipFlag flag) {
        tooltip.add(Component.translatable("tooltip.donbass.rifle_ammo", getAmmo(stack), DonbassConfig.rifleMagazine())
                .withStyle(ChatFormatting.GRAY));
        if (isReloading(stack)) {
            tooltip.add(Component.translatable("tooltip.donbass.rifle_reloading").withStyle(ChatFormatting.YELLOW));
        }
        tooltip.add(Component.translatable("tooltip.donbass.rifle_hint").withStyle(ChatFormatting.DARK_GRAY));
    }

    @Override
    public void initializeClient(Consumer<IClientItemExtensions> consumer) {
        consumer.accept(new AkClientExtensions());
    }
}

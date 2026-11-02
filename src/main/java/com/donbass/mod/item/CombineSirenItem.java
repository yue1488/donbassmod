package com.donbass.mod.item;

import com.donbass.mod.entity.CombineDirectorEntity;
import com.donbass.mod.registry.ModEntities;
import com.donbass.mod.registry.ModSounds;
import java.util.List;
import javax.annotation.Nullable;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.Difficulty;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

/**
 * The Combine Siren: the only way to call the boss. Use it on open ground; the Director steps out a few blocks
 * ahead. Not usable on Peaceful, and not while another Director is within 160 blocks.
 */
public class CombineSirenItem extends Item {
    public CombineSirenItem(Item.Properties properties) {
        super(properties);
    }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (!(level instanceof ServerLevel server)) {
            return InteractionResultHolder.sidedSuccess(stack, true);
        }
        if (server.getDifficulty() == Difficulty.PEACEFUL) {
            player.displayClientMessage(Component.translatable("message.donbass.siren_peaceful"), true);
            return InteractionResultHolder.fail(stack);
        }
        if (!server.getEntitiesOfClass(CombineDirectorEntity.class, player.getBoundingBox().inflate(160.0D)).isEmpty()) {
            player.displayClientMessage(Component.translatable("message.donbass.siren_busy"), true);
            return InteractionResultHolder.fail(stack);
        }
        Vec3 spot = findSpot(server, player);
        if (spot == null) {
            player.displayClientMessage(Component.translatable("message.donbass.siren_no_room"), true);
            return InteractionResultHolder.fail(stack);
        }

        CombineDirectorEntity boss = ModEntities.COMBINE_DIRECTOR.get().create(server);
        if (boss == null) {
            return InteractionResultHolder.fail(stack);
        }
        float yaw = (float) (Math.toDegrees(Math.atan2(player.getZ() - spot.z, player.getX() - spot.x)) - 90.0D);
        boss.moveTo(spot.x, spot.y, spot.z, yaw, 0.0F);
        boss.finalizeSpawn(server, server.getCurrentDifficultyAt(BlockPos.containing(spot)), MobSpawnType.MOB_SUMMONED,
                null, null);
        boss.setTarget(player);
        server.addFreshEntity(boss);

        server.playSound(null, spot.x, spot.y, spot.z, ModSounds.DIRECTOR_SIREN.get(), SoundSource.HOSTILE, 5.0F, 1.0F);
        server.sendParticles(ParticleTypes.LARGE_SMOKE, spot.x, spot.y + 1.0D, spot.z, 60, 1.0D, 1.2D, 1.0D, 0.06D);
        for (Player nearby : server.players()) {
            if (nearby.distanceToSqr(spot.x, spot.y, spot.z) < 64.0D * 64.0D) {
                nearby.displayClientMessage(Component.translatable("message.donbass.director_summon"), false);
            }
        }
        if (!player.getAbilities().instabuild) {
            stack.shrink(1);
        }
        player.getCooldowns().addCooldown(this, 100);
        return InteractionResultHolder.consume(stack);
    }

    /** A free standing spot 5..12 blocks in front of the player (and, failing that, to the sides), or null. */
    @Nullable
    private static Vec3 findSpot(ServerLevel level, Player player) {
        Vec3 look = player.getLookAngle();
        Vec3 flat = new Vec3(look.x, 0.0D, look.z);
        flat = flat.lengthSqr() < 1.0E-4D ? new Vec3(0.0D, 0.0D, 1.0D) : flat.normalize();
        Vec3 side = new Vec3(-flat.z, 0.0D, flat.x);
        double[] ahead = {8.0D, 6.0D, 10.0D, 5.0D, 12.0D, 8.0D, 8.0D};
        double[] aside = {0.0D, 0.0D, 0.0D, 0.0D, 0.0D, 5.0D, -5.0D};
        for (int i = 0; i < ahead.length; i++) {
            double x = player.getX() + flat.x * ahead[i] + side.x * aside[i];
            double z = player.getZ() + flat.z * ahead[i] + side.z * aside[i];
            for (int dy = 3; dy >= -4; dy--) {
                double y = Math.floor(player.getY()) + dy;
                BlockPos below = BlockPos.containing(x, y - 1.0D, z);
                if (!level.getBlockState(below).isFaceSturdy(level, below, Direction.UP)) {
                    continue;
                }
                if (level.noCollision(ModEntities.COMBINE_DIRECTOR.get().getAABB(x, y, z))) {
                    return new Vec3(x, y, z);
                }
            }
        }
        return null;
    }

    @Override
    public void appendHoverText(ItemStack stack, @Nullable Level level, List<Component> tooltip, TooltipFlag flag) {
        tooltip.add(Component.translatable("tooltip.donbass.siren").withStyle(ChatFormatting.GRAY));
        tooltip.add(Component.translatable("tooltip.donbass.siren_hint").withStyle(ChatFormatting.DARK_RED));
    }
}

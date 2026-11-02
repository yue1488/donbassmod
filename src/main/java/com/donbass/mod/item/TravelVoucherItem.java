package com.donbass.mod.item;

import com.donbass.mod.registry.ModBlocks;
import com.donbass.mod.worldgen.DonbassDimension;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.Heightmap;

/**
 * Reusable pass between the Overworld and the Donbass dimension.
 * Right-click in the Overworld to travel to the Donbass, right-click there to come back.
 */
public class TravelVoucherItem extends Item {
    private static final int COOLDOWN_TICKS = 100;
    /** Sea level of the Donbass noise settings (data/donbass/worldgen/noise_settings/steppe.json). */
    private static final int DONBASS_SEA_LEVEL = 63;
    private static final int SEARCH_STEPS = 40;
    private static final int SEARCH_STRIDE = 8;

    public TravelVoucherItem(Item.Properties properties) {
        super(properties);
    }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (level.isClientSide()) {
            return InteractionResultHolder.success(stack);
        }
        if (!(player instanceof ServerPlayer serverPlayer)) {
            return InteractionResultHolder.pass(stack);
        }

        MinecraftServer server = serverPlayer.server;
        ServerLevel target;
        BlockPos anchor;
        String messageKey;
        boolean toDonbass;

        if (level.dimension() == Level.OVERWORLD) {
            target = server.getLevel(DonbassDimension.KEY);
            anchor = BlockPos.ZERO;
            messageKey = "message.donbass.travel_to";
            toDonbass = true;
        } else if (level.dimension() == DonbassDimension.KEY) {
            target = server.overworld();
            anchor = target.getSharedSpawnPos();
            messageKey = "message.donbass.travel_back";
            toDonbass = false;
        } else {
            player.displayClientMessage(Component.translatable("message.donbass.wrong_place"), true);
            return InteractionResultHolder.fail(stack);
        }

        if (target == null) {
            player.displayClientMessage(Component.translatable("message.donbass.wrong_place"), true);
            return InteractionResultHolder.fail(stack);
        }

        BlockPos destination = toDonbass ? findDryLanding(target, anchor) : surfaceAt(target, anchor.getX(), anchor.getZ());
        serverPlayer.teleportTo(target, destination.getX() + 0.5D, destination.getY(), destination.getZ() + 0.5D,
                serverPlayer.getYRot(), serverPlayer.getXRot());
        serverPlayer.displayClientMessage(Component.translatable(messageKey), true);
        player.getCooldowns().addCooldown(this, COOLDOWN_TICKS);
        return InteractionResultHolder.success(stack);
    }

    /** First free position above the terrain surface of the given column (generates the chunk if needed). */
    private static BlockPos surfaceAt(ServerLevel level, int x, int z) {
        level.getChunk(x >> 4, z >> 4);
        return new BlockPos(x, level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, x, z), z);
    }

    /**
     * Walks along +X from the anchor until the surface is above sea level (no lake) and the block
     * underfoot is not smouldering spoil; falls back to the anchor column if nothing suitable is found.
     */
    private static BlockPos findDryLanding(ServerLevel level, BlockPos anchor) {
        for (int i = 0; i < SEARCH_STEPS; i++) {
            BlockPos candidate = surfaceAt(level, anchor.getX() + i * SEARCH_STRIDE, anchor.getZ());
            BlockState below = level.getBlockState(candidate.below());
            boolean dry = candidate.getY() > DONBASS_SEA_LEVEL && level.getFluidState(candidate.below()).isEmpty();
            if (dry && !below.is(ModBlocks.SMOLDERING_SPOIL.get())) {
                return candidate;
            }
        }
        return surfaceAt(level, anchor.getX(), anchor.getZ());
    }
}

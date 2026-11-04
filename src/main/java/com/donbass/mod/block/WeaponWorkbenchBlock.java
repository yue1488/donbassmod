package com.donbass.mod.block;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraftforge.network.NetworkHooks;

/** The Weapon Workbench: right-click opens the AK modification screen. */
public class WeaponWorkbenchBlock extends BaseEntityBlock {
    public WeaponWorkbenchBlock(BlockBehaviour.Properties properties) {
        super(properties);
    }

    /** A BaseEntityBlock is INVISIBLE by default: without this the block would render as nothing. */
    @Override
    public RenderShape getRenderShape(BlockState state) {
        return RenderShape.MODEL;
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new WeaponWorkbenchBlockEntity(pos, state);
    }

    @Override
    public InteractionResult use(BlockState state, Level level, BlockPos pos, Player player, InteractionHand hand,
                                 BlockHitResult hit) {
        if (level.isClientSide) {
            return InteractionResult.SUCCESS;
        }
        if (level.getBlockEntity(pos) instanceof WeaponWorkbenchBlockEntity bench && player instanceof ServerPlayer sp) {
            NetworkHooks.openScreen(sp, bench);
        }
        return InteractionResult.CONSUME;
    }

    @Override
    public void onRemove(BlockState state, Level level, BlockPos pos, BlockState newState, boolean isMoving) {
        if (!state.is(newState.getBlock()) && level.getBlockEntity(pos) instanceof WeaponWorkbenchBlockEntity bench) {
            bench.dropContents(level, pos);
        }
        super.onRemove(state, level, pos, newState, isMoving);
    }
}

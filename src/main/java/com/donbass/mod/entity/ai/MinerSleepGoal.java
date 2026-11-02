package com.donbass.mod.entity.ai;

import com.donbass.mod.entity.MinerEntity;
import java.util.EnumSet;
import javax.annotation.Nullable;
import net.minecraft.core.BlockPos;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BedBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.BedPart;

/** At night a miner walks to a free bed within reach and sleeps there until morning. */
public class MinerSleepGoal extends Goal {
    private static final int SEARCH_XZ = 18;
    private static final int SEARCH_Y = 4;

    private final MinerEntity miner;
    @Nullable
    private BlockPos bed;
    private int repath;

    public MinerSleepGoal(MinerEntity miner) {
        this.miner = miner;
        this.setFlags(EnumSet.of(Goal.Flag.MOVE, Goal.Flag.LOOK, Goal.Flag.JUMP));
    }

    private static boolean isNight(Level level) {
        long t = level.getDayTime() % 24000L;
        return t >= 13000L && t < 23000L;
    }

    @Override
    public boolean canUse() {
        if (miner.isTrading() || miner.getTarget() != null || miner.isBaby()
                || !isNight(miner.level()) || miner.getRandom().nextInt(reducedTickDelay(40)) != 0) {
            return false;
        }
        bed = findBed();
        return bed != null;
    }

    @Override
    public boolean canContinueToUse() {
        return bed != null && isNight(miner.level()) && !miner.isTrading() && miner.getTarget() == null
                && miner.getLastHurtByMob() == null;
    }

    @Override
    public void start() {
        repath = 0;
        walkToBed();
    }

    @Override
    public void stop() {
        if (miner.isSleeping()) {
            miner.stopSleeping();
        }
        bed = null;
        miner.getNavigation().stop();
    }

    @Override
    public boolean requiresUpdateEveryTick() {
        return true;
    }

    @Override
    public void tick() {
        if (bed == null) {
            return;
        }
        if (miner.isSleeping()) {
            return;
        }
        if (miner.distanceToSqr(bed.getX() + 0.5D, bed.getY() + 0.5D, bed.getZ() + 0.5D) < 2.6D) {
            miner.getNavigation().stop();
            BlockState state = miner.level().getBlockState(bed);
            if (state.getBlock() instanceof BedBlock && !state.getValue(BedBlock.OCCUPIED)) {
                miner.startSleeping(bed);
            } else {
                bed = null;                       // somebody took it
            }
        } else if (--repath <= 0) {
            repath = 20;
            walkToBed();
        }
    }

    private void walkToBed() {
        if (bed != null) {
            miner.getNavigation().moveTo(bed.getX() + 0.5D, bed.getY(), bed.getZ() + 0.5D, 0.6D);
        }
    }

    @Nullable
    private BlockPos findBed() {
        Level level = miner.level();
        BlockPos origin = miner.blockPosition();
        BlockPos best = null;
        double bestDist = Double.MAX_VALUE;
        for (BlockPos pos : BlockPos.betweenClosed(origin.offset(-SEARCH_XZ, -SEARCH_Y, -SEARCH_XZ),
                origin.offset(SEARCH_XZ, SEARCH_Y, SEARCH_XZ))) {
            BlockState state = level.getBlockState(pos);
            if (state.getBlock() instanceof BedBlock && state.getValue(BedBlock.PART) == BedPart.HEAD
                    && !state.getValue(BedBlock.OCCUPIED)) {
                double d = pos.distSqr(origin);
                if (d < bestDist) {
                    bestDist = d;
                    best = pos.immutable();
                }
            }
        }
        return best;
    }
}

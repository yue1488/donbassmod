package com.donbass.mod.entity.ai;

import com.donbass.mod.entity.MinerEntity;
import com.donbass.mod.registry.ModTags;
import java.util.EnumSet;
import javax.annotation.Nullable;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;

/**
 * By day a miner picks a work block (tag donbass:miner_workstations: coal seams, bunkers, furnaces, anvils...)
 * nearby, walks to it and works there for a while: swings the pickaxe, chips particles, makes noise.
 */
public class MinerWorkGoal extends Goal {
    private static final int SEARCH_XZ = 12;
    private static final int SEARCH_Y = 3;
    private static final int WORK_TICKS = 220;
    /** Gives up on a work block that cannot be reached (behind a wall, in a shaft wall...) after this many ticks. */
    private static final int APPROACH_LIMIT = 400;

    private final MinerEntity miner;
    private final double speed;
    @Nullable
    private BlockPos station;
    private int workTicks;
    private int approachTicks;
    private int repath;

    public MinerWorkGoal(MinerEntity miner, double speed) {
        this.miner = miner;
        this.speed = speed;
        this.setFlags(EnumSet.of(Goal.Flag.MOVE, Goal.Flag.LOOK));
    }

    static boolean isDay(Level level) {
        long t = level.getDayTime() % 24000L;
        return t < 12500L || t > 23500L;
    }

    @Override
    public boolean canUse() {
        if (miner.isTrading() || miner.isSleeping() || miner.getTarget() != null || miner.isBaby()) {
            return false;
        }
        if (!isDay(miner.level()) || miner.getRandom().nextInt(reducedTickDelay(90)) != 0) {
            return false;
        }
        station = findStation();
        return station != null;
    }

    @Override
    public boolean canContinueToUse() {
        return station != null && workTicks < WORK_TICKS && approachTicks < APPROACH_LIMIT && !miner.isTrading() && miner.getTarget() == null
                && isDay(miner.level()) && miner.level().getBlockState(station).is(ModTags.MINER_WORKSTATIONS);
    }

    @Override
    public void start() {
        workTicks = 0;
        approachTicks = 0;
        repath = 0;
        moveToStation();
    }

    @Override
    public void stop() {
        station = null;
        miner.getNavigation().stop();
    }

    @Override
    public boolean requiresUpdateEveryTick() {
        return true;
    }

    @Override
    public void tick() {
        if (station == null) {
            return;
        }
        Vec3 center = Vec3.atCenterOf(station);
        miner.getLookControl().setLookAt(center.x, center.y, center.z);
        if (miner.distanceToSqr(center) > 6.0D) {
            approachTicks++;
            if (--repath <= 0) {
                repath = 20;
                moveToStation();
            }
            return;
        }
        miner.getNavigation().stop();
        workTicks++;
        if (workTicks % 22 == 10) {
            miner.swing(InteractionHand.MAIN_HAND);
            Level level = miner.level();
            level.playSound(null, station, SoundEvents.STONE_HIT, SoundSource.NEUTRAL, 0.7F,
                    0.8F + miner.getRandom().nextFloat() * 0.4F);
            if (level instanceof ServerLevel server) {
                BlockState state = level.getBlockState(station);
                server.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, state), center.x, center.y, center.z,
                        6, 0.25D, 0.25D, 0.25D, 0.05D);
            }
        }
    }

    private void moveToStation() {
        if (station != null) {
            miner.getNavigation().moveTo(station.getX() + 0.5D, station.getY(), station.getZ() + 0.5D, speed);
        }
    }

    @Nullable
    private BlockPos findStation() {
        Level level = miner.level();
        BlockPos origin = miner.blockPosition();
        BlockPos best = null;
        double bestScore = Double.MAX_VALUE;
        for (BlockPos pos : BlockPos.betweenClosed(origin.offset(-SEARCH_XZ, -SEARCH_Y, -SEARCH_XZ),
                origin.offset(SEARCH_XZ, SEARCH_Y, SEARCH_XZ))) {
            if (!level.getBlockState(pos).is(ModTags.MINER_WORKSTATIONS)) {
                continue;
            }
            // nearest wins, plus some jitter so that a group does not queue at the same block
            double score = pos.distSqr(origin) + miner.getRandom().nextInt(16);
            if (score < bestScore) {
                bestScore = score;
                best = pos.immutable();
            }
        }
        return best;
    }
}

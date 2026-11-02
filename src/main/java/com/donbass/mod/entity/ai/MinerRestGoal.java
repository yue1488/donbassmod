package com.donbass.mod.entity.ai;

import com.donbass.mod.entity.MinerEntity;
import java.util.EnumSet;
import net.minecraft.world.entity.ai.goal.Goal;

/** A short break: the miner stands still, looks around and recovers a little health. */
public class MinerRestGoal extends Goal {
    private final MinerEntity miner;
    private int restTicks;

    public MinerRestGoal(MinerEntity miner) {
        this.miner = miner;
        this.setFlags(EnumSet.of(Goal.Flag.MOVE, Goal.Flag.LOOK));
    }

    @Override
    public boolean canUse() {
        return !miner.isTrading() && !miner.isSleeping() && miner.getTarget() == null
                && miner.getRandom().nextInt(reducedTickDelay(400)) == 0;
    }

    @Override
    public boolean canContinueToUse() {
        return restTicks > 0 && !miner.isTrading() && miner.getTarget() == null && miner.getLastHurtByMob() == null;
    }

    @Override
    public void start() {
        restTicks = 100 + miner.getRandom().nextInt(140);
        miner.getNavigation().stop();
    }

    @Override
    public void stop() {
        restTicks = 0;
    }

    @Override
    public void tick() {
        restTicks--;
        if (restTicks % 40 == 0 && miner.getHealth() < miner.getMaxHealth()) {
            miner.heal(1.0F);
        }
        if (restTicks % 50 == 0) {
            double angle = miner.getRandom().nextDouble() * Math.PI * 2.0D;
            miner.getLookControl().setLookAt(miner.getX() + Math.cos(angle) * 4.0D, miner.getEyeY() - 0.4D,
                    miner.getZ() + Math.sin(angle) * 4.0D);
        }
    }
}

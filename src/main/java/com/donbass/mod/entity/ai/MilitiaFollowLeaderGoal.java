package com.donbass.mod.entity.ai;

import com.donbass.mod.entity.MilitiaEntity;
import java.util.EnumSet;
import java.util.List;
import javax.annotation.Nullable;
import net.minecraft.world.entity.ai.goal.Goal;

/** Lower ranks stay near the nearest higher-ranking comrade of their own squad: a patrol moves as a group. */
public class MilitiaFollowLeaderGoal extends Goal {
    private final MilitiaEntity mob;
    private final double speed;
    @Nullable
    private MilitiaEntity leader;
    private int repath;

    public MilitiaFollowLeaderGoal(MilitiaEntity mob, double speed) {
        this.mob = mob;
        this.speed = speed;
        this.setFlags(EnumSet.of(Goal.Flag.MOVE));
    }

    @Override
    public boolean canUse() {
        if (mob.getTarget() != null || mob.getRank() >= MilitiaEntity.RANK_SERGEANT
                || mob.getRandom().nextInt(reducedTickDelay(15)) != 0) {
            return false;
        }
        List<MilitiaEntity> near = mob.level().getEntitiesOfClass(MilitiaEntity.class,
                mob.getBoundingBox().inflate(20.0D, 6.0D, 20.0D),
                other -> other != mob && other.isAlive() && other.getFaction() == mob.getFaction()
                        && other.getRank() > mob.getRank());
        MilitiaEntity best = null;
        double bestDist = Double.MAX_VALUE;
        for (MilitiaEntity other : near) {
            double d = mob.distanceToSqr(other);
            if (d < bestDist) {
                bestDist = d;
                best = other;
            }
        }
        if (best == null || bestDist < 25.0D) {
            return false;                              // nobody to follow, or already close enough
        }
        leader = best;
        return true;
    }

    @Override
    public boolean canContinueToUse() {
        return leader != null && leader.isAlive() && mob.getTarget() == null && mob.distanceToSqr(leader) > 9.0D;
    }

    @Override
    public void start() {
        repath = 0;
    }

    @Override
    public void stop() {
        leader = null;
        mob.getNavigation().stop();
    }

    @Override
    public void tick() {
        if (leader != null && --repath <= 0) {
            repath = 10;
            mob.getNavigation().moveTo(leader, speed);
        }
    }
}

package com.donbass.mod.entity.ai;

import com.donbass.mod.entity.MilitiaEntity;
import java.util.EnumSet;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.goal.Goal;

/**
 * Ranged combat: closes in until it has a line of sight, then keeps a comfortable distance, strafes and shoots
 * bursts (the shooting itself is MilitiaEntity.tickCombat). Backs off if the target comes too close and hits
 * with the rifle butt at point-blank range.
 */
public class MilitiaRifleGoal extends Goal {
    private static final double PREFERRED = 15.0D;
    private static final double TOO_CLOSE = 6.0D;

    private final MilitiaEntity mob;
    private int seeTime;
    private int strafeTicks;
    private boolean strafeRight;
    private int repath;
    private int meleeCooldown;

    public MilitiaRifleGoal(MilitiaEntity mob) {
        this.mob = mob;
        this.setFlags(EnumSet.of(Goal.Flag.MOVE, Goal.Flag.LOOK));
    }

    @Override
    public boolean canUse() {
        LivingEntity target = mob.getTarget();
        return target != null && target.isAlive() && mob.isHoldingRifle();
    }

    @Override
    public boolean canContinueToUse() {
        return canUse();
    }

    @Override
    public void start() {
        mob.setAggressive(true);
        seeTime = 0;
        repath = 0;
    }

    @Override
    public void stop() {
        mob.setAggressive(false);
        mob.getNavigation().stop();
        seeTime = 0;
    }

    @Override
    public boolean requiresUpdateEveryTick() {
        return true;
    }

    @Override
    public void tick() {
        LivingEntity target = mob.getTarget();
        if (target == null) {
            return;
        }
        double distance = Math.sqrt(mob.distanceToSqr(target));
        boolean canSee = mob.getSensing().hasLineOfSight(target);
        seeTime = canSee ? seeTime + 1 : 0;
        mob.getLookControl().setLookAt(target, 40.0F, 40.0F);

        if (meleeCooldown > 0) {
            meleeCooldown--;
        }
        if (distance < 2.4D && meleeCooldown == 0) {
            mob.swing(net.minecraft.world.InteractionHand.MAIN_HAND);
            mob.doHurtTarget(target);
            meleeCooldown = 20;
        }

        if (canSee && distance <= PREFERRED && seeTime >= 8) {
            mob.getNavigation().stop();
            if (--strafeTicks <= 0) {
                strafeTicks = 20 + mob.getRandom().nextInt(40);
                strafeRight = mob.getRandom().nextBoolean();
            }
            // MoveControl.strafe reuses the last speed modifier: make sure it is not zero
            mob.getMoveControl().setWantedPosition(mob.getX(), mob.getY(), mob.getZ(), 1.0D);
            mob.getMoveControl().strafe(distance < TOO_CLOSE ? -0.6F : 0.0F, strafeRight ? 0.45F : -0.45F);
        } else if (--repath <= 0) {
            repath = 8 + mob.getRandom().nextInt(6);
            mob.getNavigation().moveTo(target, 1.0D);
        }
        mob.tickCombat(target, canSee, distance);
    }
}

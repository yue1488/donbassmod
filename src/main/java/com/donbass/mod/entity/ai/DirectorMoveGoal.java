package com.donbass.mod.entity.ai;

import com.donbass.mod.entity.CombineDirectorEntity;
import java.util.EnumSet;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.util.DefaultRandomPos;
import net.minecraft.world.phys.Vec3;

/**
 * Movement of the boss. Phase 1: keeps 8..15 blocks away, strafes and backs off. Phases 2 and 3: chases the target
 * and hits it in melee. (Shooting, slams and strikes are timed by the entity itself.)
 */
public class DirectorMoveGoal extends Goal {
    private final CombineDirectorEntity boss;
    private int repath;
    private int strafeTicks;
    private boolean strafeRight;
    private int meleeCooldown;

    public DirectorMoveGoal(CombineDirectorEntity boss) {
        this.boss = boss;
        this.setFlags(EnumSet.of(Goal.Flag.MOVE, Goal.Flag.LOOK));
    }

    @Override
    public boolean canUse() {
        LivingEntity target = boss.getTarget();
        return target != null && target.isAlive();
    }

    @Override
    public boolean canContinueToUse() {
        return canUse();
    }

    @Override
    public boolean requiresUpdateEveryTick() {
        return true;
    }

    @Override
    public void start() {
        repath = 0;
    }

    @Override
    public void stop() {
        boss.getNavigation().stop();
    }

    @Override
    public void tick() {
        LivingEntity target = boss.getTarget();
        if (target == null) {
            return;
        }
        double distance = Math.sqrt(boss.distanceToSqr(target));
        boolean canSee = boss.getSensing().hasLineOfSight(target);
        int phase = boss.getPhase();
        boss.getLookControl().setLookAt(target, 30.0F, 30.0F);
        if (boss.isLocked()) {                       // phase change or slam wind-up: stand still, do not strike
            boss.getNavigation().stop();
            return;
        }
        if (meleeCooldown > 0) {
            meleeCooldown--;
        }

        if (phase == 1) {
            if (!canSee || distance > 15.0D) {
                if (--repath <= 0) {
                    repath = 8 + boss.getRandom().nextInt(5);
                    boss.getNavigation().moveTo(target, 1.0D);
                }
            } else if (distance < 8.0D) {
                if (--repath <= 0) {
                    repath = 15;
                    Vec3 away = DefaultRandomPos.getPosAway(boss, 10, 4, target.position());
                    if (away != null) {
                        boss.getNavigation().moveTo(away.x, away.y, away.z, 1.15D);
                    }
                }
            } else {
                boss.getNavigation().stop();
                if (--strafeTicks <= 0) {
                    strafeTicks = 20 + boss.getRandom().nextInt(40);
                    strafeRight = boss.getRandom().nextBoolean();
                }
                boss.getMoveControl().setWantedPosition(boss.getX(), boss.getY(), boss.getZ(), 1.0D);
                boss.getMoveControl().strafe(0.0F, strafeRight ? 0.4F : -0.4F);
            }
        } else if (--repath <= 0) {
            repath = 6 + boss.getRandom().nextInt(5);
            boss.getNavigation().moveTo(target, phase == 2 ? 1.1D : 1.25D);
        }

        if (distance < 3.4D && meleeCooldown == 0) {
            boss.swing(InteractionHand.MAIN_HAND);
            boss.doHurtTarget(target);
            meleeCooldown = phase == 3 ? 14 : 20;
        }
    }
}

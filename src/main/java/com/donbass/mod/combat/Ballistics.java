package com.donbass.mod.combat;

import java.util.function.Predicate;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.ProjectileUtil;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.EntityHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

/** Hitscan bullets shared by the player's rifle and the fighters. Server side only. */
public final class Ballistics {
    private Ballistics() {}

    /** Random direction inside a cone of the given half-angle (degrees) around dir. */
    public static Vec3 spread(RandomSource random, Vec3 dir, double degrees) {
        if (degrees <= 0.0D) {
            return dir.normalize();
        }
        double s = Math.tan(Math.toRadians(degrees)) * 0.5D;
        Vec3 d = dir.normalize();
        return new Vec3(d.x + random.nextGaussian() * s, d.y + random.nextGaussian() * s,
                d.z + random.nextGaussian() * s).normalize();
    }

    /** Default target filter: anything solid enough to be hit that is not the shooter. */
    public static Predicate<Entity> defaultFilter(Entity shooter) {
        return e -> e != shooter && !e.isSpectator() && e.isPickable() && !(e instanceof ItemEntity);
    }

    /**
     * Fires one bullet. Returns the entity that was hit, or null. Spawns impact particles and applies
     * the damage with the invulnerability frames reset, so that automatic fire is not swallowed by them.
     */
    public static Entity shoot(Level level, LivingEntity shooter, Vec3 origin, Vec3 dir, double range, float damage,
                               Predicate<Entity> filter) {
        Vec3 end = origin.add(dir.scale(range));
        BlockHitResult blockHit = level.clip(new ClipContext(origin, end, ClipContext.Block.COLLIDER,
                ClipContext.Fluid.NONE, shooter));
        Vec3 limit = blockHit.getType() == HitResult.Type.MISS ? end : blockHit.getLocation();
        AABB box = new AABB(origin, limit).inflate(1.0D);
        EntityHitResult entityHit = ProjectileUtil.getEntityHitResult(level, shooter, origin, limit, box, filter);

        if (entityHit != null) {
            Entity target = entityHit.getEntity();
            DamageSource source = shooter instanceof Player player
                    ? level.damageSources().playerAttack(player)
                    : level.damageSources().mobAttack(shooter);
            Vec3 motion = target.getDeltaMovement();
            if (target instanceof LivingEntity living) {
                living.invulnerableTime = 0;
            }
            boolean hurt = target.hurt(source, damage);
            if (hurt && target instanceof LivingEntity) {
                // keep the knockback of a bullet small: restore the old motion plus a gentle push
                target.setDeltaMovement(motion.add(dir.scale(0.06D)));
            }
            if (level instanceof ServerLevel server) {
                Vec3 p = entityHit.getLocation();
                server.sendParticles(ParticleTypes.CRIT, p.x, p.y, p.z, 3, 0.1D, 0.1D, 0.1D, 0.05D);
            }
            return target;
        }
        if (blockHit.getType() == HitResult.Type.BLOCK && level instanceof ServerLevel server) {
            BlockPos pos = blockHit.getBlockPos();
            BlockState state = level.getBlockState(pos);
            Vec3 p = blockHit.getLocation();
            server.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, state), p.x, p.y, p.z,
                    6, 0.08D, 0.08D, 0.08D, 0.05D);
            server.sendParticles(ParticleTypes.SMOKE, p.x, p.y, p.z, 1, 0.02D, 0.02D, 0.02D, 0.0D);
        }
        return null;
    }
}

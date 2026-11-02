package com.donbass.mod.entity;

import com.donbass.mod.combat.Ballistics;
import com.donbass.mod.config.DonbassConfig;
import com.donbass.mod.entity.ai.DirectorMoveGoal;
import com.donbass.mod.item.AkRifleItem;
import com.donbass.mod.registry.ModEntities;
import com.donbass.mod.registry.ModItems;
import com.donbass.mod.registry.ModSounds;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import javax.annotation.Nullable;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundStopSoundPacket;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerBossEvent;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.util.Mth;
import net.minecraft.world.BossEvent;
import net.minecraft.world.DifficultyInstance;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.entity.SpawnGroupData;
import net.minecraft.world.entity.ai.attributes.Attribute;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.ServerLevelAccessor;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

/**
 * The Combine Director - the boss (a fictional character). Called only with the Combine Siren, never spawns on its
 * own. Three phases by health (above 2/3, above 1/3, below), each with its own attacks, music and boss bar colour:
 * <ol>
 *   <li>The Briefing: keeps its distance and fires rifle bursts, calls two guards now and then.</li>
 *   <li>All Hands: closes in, hits hard in melee, slams the ground (a telegraphed shockwave) between bursts.</li>
 *   <li>Fire in the Face: faster, burns everybody close to it, drops warned strikes on every player, slams more often.</li>
 * </ol>
 * The coal armour set (fire resistance) is the natural counter to phase three.
 */
public class CombineDirectorEntity extends Monster {
    public static final int POSE_NORMAL = 0;
    public static final int POSE_SLAM = 1;
    public static final int POSE_ROAR = 2;

    /** Length of the generated music loops (tools/gen_sounds.py: MUSIC_SECONDS = 16). */
    private static final int MUSIC_LOOP_TICKS = 320;
    /** A single hit never takes more than this (commands that bypass invulnerability are not capped). */
    private static final float MAX_HIT = 40.0F;

    private static final EntityDataAccessor<Integer> DATA_PHASE =
            SynchedEntityData.defineId(CombineDirectorEntity.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Integer> DATA_POSE =
            SynchedEntityData.defineId(CombineDirectorEntity.class, EntityDataSerializers.INT);

    private final ServerBossEvent bossEvent = new ServerBossEvent(
            Component.translatable("entity.donbass.combine_director"),
            BossEvent.BossBarColor.YELLOW, BossEvent.BossBarOverlay.NOTCHED_6);

    private static final class Strike {
        final double x;
        final double y;
        final double z;
        int delay;

        Strike(double x, double y, double z, int delay) {
            this.x = x;
            this.y = y;
            this.z = z;
            this.delay = delay;
        }
    }

    private final List<Strike> strikes = new ArrayList<>();
    private boolean initialized;
    private int transition;
    private int musicTimer;
    private int shotCd = 40;
    private int burstLeft;
    private int burstGap;
    private int slamCd = 120;
    private int slamWindup;
    private int strikeCd = 60;
    private int summonCd = 300;
    private int idleTicks;

    public CombineDirectorEntity(EntityType<? extends CombineDirectorEntity> type, Level level) {
        super(type, level);
        this.xpReward = 500;
        this.setPersistenceRequired();
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 320.0D)
                .add(Attributes.MOVEMENT_SPEED, 0.27D)
                .add(Attributes.ATTACK_DAMAGE, 9.0D)
                .add(Attributes.FOLLOW_RANGE, 48.0D)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0D)
                .add(Attributes.ARMOR, 8.0D)
                .add(Attributes.ARMOR_TOUGHNESS, 4.0D);
    }

    // ------------------------------------------------------------- state ----
    @Override
    protected void defineSynchedData() {
        super.defineSynchedData();
        this.entityData.define(DATA_PHASE, 1);
        this.entityData.define(DATA_POSE, POSE_NORMAL);
    }

    public int getPhase() {
        return this.entityData.get(DATA_PHASE);
    }

    public int getBossPose() {
        return this.entityData.get(DATA_POSE);
    }

    private void setBossPose(int pose) {
        if (this.entityData.get(DATA_POSE) != pose) {
            this.entityData.set(DATA_POSE, pose);
        }
    }

    public boolean isHoldingRifle() {
        return this.getMainHandItem().getItem() instanceof AkRifleItem;
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(0, new FloatGoal(this));
        this.goalSelector.addGoal(1, new DirectorMoveGoal(this));
        this.goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 24.0F));
        this.goalSelector.addGoal(7, new RandomLookAroundGoal(this));
        this.targetSelector.addGoal(1, new HurtByTargetGoal(this));
        this.targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, false));
    }

    @Override
    public SpawnGroupData finalizeSpawn(ServerLevelAccessor level, DifficultyInstance difficulty,
                                                                   MobSpawnType reason, @Nullable SpawnGroupData spawnData,
                                                                   @Nullable CompoundTag tag) {
        SpawnGroupData data = super.finalizeSpawn(level, difficulty, reason, spawnData, tag);
        setUp();
        return data;
    }

    /** Health from the config, the rifle and the coal armour (none of it drops: the loot table decides). */
    private void setUp() {
        if (initialized) {
            return;
        }
        initialized = true;
        setBase(Attributes.MAX_HEALTH, DonbassConfig.bossHealth());
        this.setHealth(this.getMaxHealth());
        applyPhaseStats(getPhase());
        ItemStack rifle = new ItemStack(ModItems.AK_RIFLE.get());
        AkRifleItem.setAmmo(rifle, 30);
        this.setItemSlot(EquipmentSlot.MAINHAND, rifle);
        this.setItemSlot(EquipmentSlot.HEAD, new ItemStack(ModItems.COAL_HELMET.get()));
        this.setItemSlot(EquipmentSlot.CHEST, new ItemStack(ModItems.COAL_CHESTPLATE.get()));
        this.setItemSlot(EquipmentSlot.LEGS, new ItemStack(ModItems.COAL_LEGGINGS.get()));
        this.setItemSlot(EquipmentSlot.FEET, new ItemStack(ModItems.COAL_BOOTS.get()));
        for (EquipmentSlot slot : EquipmentSlot.values()) {
            this.setDropChance(slot, 0.0F);
        }
        applyBossBar();
    }

    private void setBase(Attribute attribute, double value) {
        AttributeInstance instance = this.getAttribute(attribute);
        if (instance != null) {
            instance.setBaseValue(value);
        }
    }

    private void applyPhaseStats(int phase) {
        setBase(Attributes.MOVEMENT_SPEED, phase == 1 ? 0.27D : phase == 2 ? 0.30D : 0.33D);
        setBase(Attributes.ATTACK_DAMAGE,
                (phase == 1 ? 9.0D : phase == 2 ? 11.0D : 14.0D) * DonbassConfig.bossDamageMultiplier());
    }

    private Component phaseTitle() {
        return Component.translatable("entity.donbass.combine_director").append(Component.literal(" - "))
                .append(Component.translatable("boss.donbass.phase" + getPhase()));
    }

    private void applyBossBar() {
        int phase = getPhase();
        this.bossEvent.setName(phaseTitle());
        this.bossEvent.setColor(phase == 1 ? BossEvent.BossBarColor.YELLOW
                : phase == 2 ? BossEvent.BossBarColor.RED : BossEvent.BossBarColor.PURPLE);
        this.bossEvent.setDarkenScreen(phase == 3);
    }

    private float difficultyFactor() {
        return switch (this.level().getDifficulty()) {
            case EASY -> 0.7F;
            case HARD -> 1.25F;
            default -> 1.0F;
        };
    }

    private float damageScale() {
        return (float) DonbassConfig.bossDamageMultiplier() * difficultyFactor();
    }

    // ------------------------------------------------------------ the fight ----
    @Override
    protected void customServerAiStep() {
        super.customServerAiStep();
        if (!initialized) {
            setUp();
        }
        this.bossEvent.setProgress(Mth.clamp(this.getHealth() / this.getMaxHealth(), 0.0F, 1.0F));
        updatePhase();
        tickMusic();
        tickStrikes();
        if (transition > 0) {
            tickTransition();
            return;
        }
        LivingEntity target = this.getTarget();
        if (target == null || !target.isAlive()) {
            idleTicks++;
            if (slamWindup > 0) {
                slamWindup = 0;
                setBossPose(POSE_NORMAL);
            }
            if (idleTicks > 100 && this.tickCount % 20 == 0) {
                this.heal(3.0F);                       // nobody to fight: it recovers, but never goes back a phase
            }
            return;
        }
        idleTicks = 0;
        int phase = getPhase();
        tickRifle(target, phase);
        if (phase >= 2) {
            tickSlam(target, phase);
        }
        if (phase >= 3) {
            tickStrikePlanner();
            tickHeat();
        }
        tickSummon(target, phase);
    }

    private void updatePhase() {
        float fraction = this.getHealth() / this.getMaxHealth();
        int wanted = fraction > 0.66F ? 1 : fraction > 0.33F ? 2 : 3;
        if (wanted > getPhase()) {
            enterPhase(wanted);
        }
    }

    private void enterPhase(int phase) {
        this.entityData.set(DATA_PHASE, phase);
        this.transition = 60;
        this.slamWindup = 0;
        this.burstLeft = 0;
        this.strikes.clear();
        this.getNavigation().stop();
        setBossPose(POSE_ROAR);
        applyPhaseStats(phase);
        applyBossBar();
        this.playSound(ModSounds.DIRECTOR_ROAR.get(), 4.0F, 1.0F);
        broadcast(Component.translatable("message.donbass.director_phase" + phase));
        stopMusic();
        this.musicTimer = 0;                           // the new track starts on the next tick
        shotCd = 50;
        slamCd = 70;
        strikeCd = 80;
        if (this.level() instanceof ServerLevel server) {
            server.sendParticles(ParticleTypes.EXPLOSION, getX(), getY() + 1.2D, getZ(), 6, 1.2D, 0.8D, 1.2D, 0.0D);
            server.sendParticles(ParticleTypes.LARGE_SMOKE, getX(), getY() + 1.0D, getZ(), 50, 1.5D, 1.0D, 1.5D, 0.05D);
        }
    }

    private void tickTransition() {
        transition--;
        if (this.level() instanceof ServerLevel server && transition % 6 == 0) {
            server.sendParticles(getPhase() == 3 ? ParticleTypes.FLAME : ParticleTypes.LARGE_SMOKE,
                    getX(), getY() + 1.0D, getZ(), 14, 0.9D, 1.0D, 0.9D, 0.04D);
        }
        if (transition == 0) {
            setBossPose(POSE_NORMAL);
        }
    }

    // ----- rifle -----
    private void tickRifle(LivingEntity target, int phase) {
        if (burstLeft > 0) {
            if (--burstGap <= 0) {
                fireShot(target, phase);
                burstLeft--;
                burstGap = phase == 3 ? 3 : 4;
            }
            return;
        }
        if (--shotCd <= 0 && slamWindup == 0 && this.hasLineOfSight(target) && this.distanceTo(target) < 40.0F) {
            burstLeft = phase == 1 ? 6 : phase == 2 ? 4 : 8;
            burstGap = 0;
            shotCd = phase == 1 ? 60 : phase == 2 ? 100 : 70;
        }
    }

    private void fireShot(LivingEntity target, int phase) {
        Vec3 origin = this.getEyePosition().add(0.0D, -0.3D, 0.0D);
        Vec3 aim = target.getBoundingBox().getCenter();
        Vec3 dir = Ballistics.spread(this.random, aim.subtract(origin).normalize(), 2.2D);
        float damage = (phase == 1 ? 4.0F : phase == 2 ? 4.5F : 5.5F) * damageScale();
        Ballistics.shoot(this.level(), this, origin, dir, 48.0D, damage, e -> e != this && !e.isSpectator()
                && e.isPickable() && !(e instanceof ItemEntity) && !(e instanceof MilitiaEntity)
                && !(e instanceof CombineDirectorEntity));
        this.level().playSound(null, getX(), getY(), getZ(), ModSounds.AK_SHOT.get(), SoundSource.HOSTILE, 1.4F, 0.8F);
        this.swing(InteractionHand.MAIN_HAND);
    }

    // ----- ground slam (phase 2+) -----
    private void tickSlam(LivingEntity target, int phase) {
        if (slamWindup > 0) {
            slamWindup--;
            if (this.level() instanceof ServerLevel server) {
                server.sendParticles(ParticleTypes.CRIT, getX(), getY() + 2.7D, getZ(), 4, 0.5D, 0.2D, 0.5D, 0.1D);
            }
            if (slamWindup == 0) {
                doSlam(phase);
                setBossPose(POSE_NORMAL);
                slamCd = phase == 2 ? 150 : 110;
            }
            return;
        }
        if (--slamCd <= 0 && this.distanceTo(target) < 9.0F) {
            slamWindup = 28;
            burstLeft = 0;
            setBossPose(POSE_SLAM);
            this.getNavigation().stop();
            this.playSound(SoundEvents.IRON_GOLEM_ATTACK, 2.0F, 0.6F);
        }
    }

    private void doSlam(int phase) {
        double radius = phase == 2 ? 7.0D : 8.5D;
        float damage = (phase == 2 ? 9.0F : 12.0F) * damageScale();
        this.level().playSound(null, getX(), getY(), getZ(), ModSounds.DIRECTOR_SLAM.get(), SoundSource.HOSTILE, 3.0F, 1.0F);
        AABB box = this.getBoundingBox().inflate(radius, 3.0D, radius);
        for (Player player : this.level().getEntitiesOfClass(Player.class, box, p -> !p.isSpectator() && p.isAlive())) {
            if (player.distanceToSqr(getX(), player.getY(), getZ()) > radius * radius) {
                continue;
            }
            player.hurt(this.damageSources().mobAttack(this), damage);
            Vec3 away = new Vec3(player.getX() - getX(), 0.0D, player.getZ() - getZ());
            away = away.lengthSqr() < 1.0E-4D ? new Vec3(1.0D, 0.0D, 0.0D) : away.normalize().scale(1.1D);
            player.setDeltaMovement(player.getDeltaMovement().add(away.x, 0.5D, away.z));
            player.hurtMarked = true;
        }
        if (this.level() instanceof ServerLevel server) {
            for (double r = 1.5D; r <= radius; r += 1.5D) {
                int n = (int) (r * 6.0D);
                for (int i = 0; i < n; i++) {
                    double a = i * (Math.PI * 2.0D / n);
                    server.sendParticles(ParticleTypes.LARGE_SMOKE, getX() + Math.cos(a) * r, getY() + 0.15D,
                            getZ() + Math.sin(a) * r, 1, 0.05D, 0.05D, 0.05D, 0.01D);
                }
            }
            server.sendParticles(ParticleTypes.EXPLOSION, getX(), getY() + 0.3D, getZ(), 3, 1.0D, 0.1D, 1.0D, 0.0D);
        }
    }

    // ----- collapse strikes and heat (phase 3) -----
    private void tickStrikePlanner() {
        if (--strikeCd > 0) {
            return;
        }
        strikeCd = 110;
        List<Player> players = this.level().getEntitiesOfClass(Player.class, this.getBoundingBox().inflate(40.0D),
                p -> !p.isSpectator() && p.isAlive());
        for (Player player : players) {
            strikes.add(new Strike(player.getX(), player.getY(), player.getZ(), 36));
            for (int i = 0; i < 2; i++) {
                strikes.add(new Strike(player.getX() + (this.random.nextDouble() - 0.5D) * 10.0D, player.getY(),
                        player.getZ() + (this.random.nextDouble() - 0.5D) * 10.0D, 36 + 6 * i));
            }
        }
    }

    private void tickStrikes() {
        if (strikes.isEmpty() || !(this.level() instanceof ServerLevel server)) {
            return;
        }
        Iterator<Strike> it = strikes.iterator();
        while (it.hasNext()) {
            Strike s = it.next();
            s.delay--;
            if (s.delay % 3 == 0) {                    // the warning: a ring of flames and a lava drip in the middle
                for (int i = 0; i < 10; i++) {
                    double a = i * (Math.PI * 2.0D / 10.0D);
                    server.sendParticles(ParticleTypes.FLAME, s.x + Math.cos(a) * 2.5D, s.y + 0.1D,
                            s.z + Math.sin(a) * 2.5D, 1, 0.0D, 0.0D, 0.0D, 0.0D);
                }
                server.sendParticles(ParticleTypes.LAVA, s.x, s.y + 0.2D, s.z, 1, 0.8D, 0.1D, 0.8D, 0.0D);
            }
            if (s.delay <= 0) {
                detonate(server, s);
                it.remove();
            }
        }
    }

    /** The strike lands: damage in a small radius, no block damage. */
    private void detonate(ServerLevel server, Strike s) {
        AABB box = new AABB(s.x - 2.8D, s.y - 1.5D, s.z - 2.8D, s.x + 2.8D, s.y + 2.5D, s.z + 2.8D);
        float damage = 11.0F * damageScale();
        for (Player player : server.getEntitiesOfClass(Player.class, box, p -> !p.isSpectator() && p.isAlive())) {
            player.hurt(this.damageSources().mobAttack(this), damage);
        }
        server.playSound(null, s.x, s.y, s.z, SoundEvents.GENERIC_EXPLODE, SoundSource.HOSTILE, 1.4F, 0.9F);
        server.sendParticles(ParticleTypes.EXPLOSION, s.x, s.y + 0.5D, s.z, 2, 0.8D, 0.2D, 0.8D, 0.0D);
        server.sendParticles(ParticleTypes.LAVA, s.x, s.y + 0.4D, s.z, 10, 1.0D, 0.3D, 1.0D, 0.0D);
        server.sendParticles(ParticleTypes.LARGE_SMOKE, s.x, s.y + 0.5D, s.z, 12, 1.0D, 0.5D, 1.0D, 0.03D);
    }

    /** Anybody close to the boss in phase 3 is set on fire: coal armour (fire resistance) counters it. */
    private void tickHeat() {
        if (this.tickCount % 40 != 0) {
            return;
        }
        for (Player player : this.level().getEntitiesOfClass(Player.class, this.getBoundingBox().inflate(4.5D),
                p -> !p.isSpectator() && p.isAlive())) {
            player.setSecondsOnFire(4);
        }
    }

    // ----- guards (phase 1 and 2) -----
    private void tickSummon(LivingEntity target, int phase) {
        if (phase >= 3 || --summonCd > 0) {
            return;
        }
        summonCd = phase == 1 ? 560 : 720;
        if (!(this.level() instanceof ServerLevel server)) {
            return;
        }
        if (server.getEntitiesOfClass(MilitiaEntity.class, this.getBoundingBox().inflate(40.0D)).size() >= 4) {
            return;
        }
        for (int i = 0; i < 2; i++) {
            MilitiaEntity guard = ModEntities.NORTH_FIGHTER.get().create(server);
            if (guard == null) {
                continue;
            }
            double angle = this.random.nextDouble() * Math.PI * 2.0D;
            double dist = 4.0D + this.random.nextDouble() * 2.0D;
            double x = getX() + Math.cos(angle) * dist;
            double z = getZ() + Math.sin(angle) * dist;
            guard.moveTo(x, getY(), z, this.random.nextFloat() * 360.0F, 0.0F);
            if (!server.noCollision(guard)) {
                continue;
            }
            guard.finalizeSpawn(server, server.getCurrentDifficultyAt(BlockPos.containing(x, getY(), z)),
                    MobSpawnType.MOB_SUMMONED, null, null);
            guard.setTarget(target);
            server.addFreshEntity(guard);
            server.sendParticles(ParticleTypes.POOF, x, getY() + 1.0D, z, 12, 0.3D, 0.5D, 0.3D, 0.05D);
        }
    }

    // ----------------------------------------------------- damage rules ----
    @Override
    public boolean hurt(DamageSource source, float amount) {
        boolean bypass = source.is(DamageTypeTags.BYPASSES_INVULNERABILITY);
        if (!bypass && (transition > 0 || source.is(DamageTypeTags.IS_FIRE) || source.is(DamageTypeTags.IS_DROWNING))) {
            return false;
        }
        return super.hurt(source, bypass ? amount : Math.min(amount, MAX_HIT));
    }

    @Override
    protected boolean isImmobile() {
        return super.isImmobile() || transition > 0 || slamWindup > 0;
    }

    @Override
    public boolean canChangeDimensions() {
        return false;
    }

    @Override
    public boolean removeWhenFarAway(double distanceToClosestPlayer) {
        return false;
    }

    @Override
    public void die(DamageSource source) {
        super.die(source);
        if (!this.level().isClientSide) {
            this.bossEvent.setProgress(0.0F);
            broadcast(Component.translatable("message.donbass.director_defeated"));
            stopMusic();
        }
    }

    @Override
    public void remove(Entity.RemovalReason reason) {
        if (!this.level().isClientSide) {
            stopMusic();
            this.bossEvent.removeAllPlayers();
        }
        super.remove(reason);
    }

    // ------------------------------------------------- boss bar and music ----
    @Override
    public void startSeenByPlayer(ServerPlayer player) {
        super.startSeenByPlayer(player);
        this.bossEvent.addPlayer(player);
        player.playNotifySound(currentTrack(), SoundSource.MUSIC, 0.9F, 1.0F);
    }

    @Override
    public void stopSeenByPlayer(ServerPlayer player) {
        super.stopSeenByPlayer(player);
        this.bossEvent.removePlayer(player);
        player.connection.send(new ClientboundStopSoundPacket(null, SoundSource.MUSIC));
    }

    private SoundEvent currentTrack() {
        return switch (getPhase()) {
            case 1 -> ModSounds.MUSIC_DIRECTOR_1.get();
            case 2 -> ModSounds.MUSIC_DIRECTOR_2.get();
            default -> ModSounds.MUSIC_DIRECTOR_3.get();
        };
    }

    /** Every loop restart stops the old music (its length is MUSIC_LOOP_TICKS) and starts the track of the phase. */
    private void tickMusic() {
        if (this.bossEvent.getPlayers().isEmpty() || --musicTimer > 0) {
            return;
        }
        musicTimer = MUSIC_LOOP_TICKS;
        SoundEvent track = currentTrack();
        for (ServerPlayer player : this.bossEvent.getPlayers()) {
            player.connection.send(new ClientboundStopSoundPacket(null, SoundSource.MUSIC));
            player.playNotifySound(track, SoundSource.MUSIC, 0.9F, 1.0F);
        }
    }

    private void stopMusic() {
        for (ServerPlayer player : this.bossEvent.getPlayers()) {
            player.connection.send(new ClientboundStopSoundPacket(null, SoundSource.MUSIC));
        }
    }

    private void broadcast(Component message) {
        for (ServerPlayer player : this.bossEvent.getPlayers()) {
            player.displayClientMessage(message, false);
        }
    }

    // ----------------------------------------------------------- visuals ----
    @Override
    public void aiStep() {
        super.aiStep();
        if (this.level().isClientSide && getPhase() >= 2 && this.random.nextInt(2) == 0) {
            this.level().addParticle(getPhase() == 3 ? ParticleTypes.FLAME : ParticleTypes.LARGE_SMOKE,
                    this.getRandomX(0.6D), this.getRandomY(), this.getRandomZ(0.6D), 0.0D, 0.03D, 0.0D);
        }
    }

    // ------------------------------------------------------------ sounds ----
    @Override
    protected SoundEvent getAmbientSound() {
        return ModSounds.DIRECTOR_AMBIENT.get();
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return ModSounds.DIRECTOR_HURT.get();
    }

    @Override
    protected SoundEvent getDeathSound() {
        return ModSounds.DIRECTOR_DEATH.get();
    }

    @Override
    protected float getSoundVolume() {
        return 2.0F;
    }

    // --------------------------------------------------------------- NBT ----
    @Override
    public void addAdditionalSaveData(CompoundTag tag) {
        super.addAdditionalSaveData(tag);
        tag.putInt("Phase", getPhase());
        tag.putBoolean("SetUp", initialized);
    }

    @Override
    public void readAdditionalSaveData(CompoundTag tag) {
        super.readAdditionalSaveData(tag);
        if (tag.contains("Phase")) {
            this.entityData.set(DATA_PHASE, Math.max(1, Math.min(3, tag.getInt("Phase"))));
        }
        this.initialized = tag.getBoolean("SetUp");
        applyBossBar();
    }
}

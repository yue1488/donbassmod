package com.donbass.mod.entity;

import com.donbass.mod.combat.Ballistics;
import com.donbass.mod.config.DonbassConfig;
import com.donbass.mod.entity.ai.MilitiaFollowLeaderGoal;
import com.donbass.mod.entity.ai.MilitiaRifleGoal;
import com.donbass.mod.item.AkRifleItem;
import com.donbass.mod.registry.ModItems;
import com.donbass.mod.registry.ModSounds;
import javax.annotation.Nullable;
import net.minecraft.core.BlockPos;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.Difficulty;
import net.minecraft.world.DifficultyInstance;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.entity.SpawnGroupData;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.MoveTowardsRestrictionGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.ServerLevelAccessor;
import net.minecraft.world.phys.Vec3;

/**
 * A militiaman: "Ополченец ДНР" (entity north_fighter, "Steppe" uniform) or "Ополченец ЛНР" (south_fighter, "Terricone" uniform).
 * Three ranks with their own health, damage, accuracy, equipment and drops. The fighters shoot with a rifle
 * (hitscan, see Ballistics), patrol around the place they were created at, follow a higher-ranking comrade,
 * call their squad when hurt and attack the other squad on sight.
 */
public class MilitiaEntity extends Monster {
    public enum Faction { NORTH, SOUTH }

    /** Ranks: recruit (weak), fighter, sergeant (leader, best gear). */
    public static final int RANK_RECRUIT = 0;
    public static final int RANK_FIGHTER = 1;
    public static final int RANK_SERGEANT = 2;

    public static final int STATE_IDLE = 0;
    public static final int STATE_AIMING = 1;
    public static final int STATE_FIRING = 2;
    public static final int STATE_RELOADING = 3;

    private static final EntityDataAccessor<Integer> DATA_RANK =
            SynchedEntityData.defineId(MilitiaEntity.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Integer> DATA_STATE =
            SynchedEntityData.defineId(MilitiaEntity.class, EntityDataSerializers.INT);

    private final Faction faction;
    private int ammo = 30;
    private int reloadTicks;
    private int firingDisplay;
    private int aimTicks;
    private int burstLeft;
    private int betweenShots;
    private int pause;
    private boolean initialized;
    /** True when the entity came from a structure template (rank written into its NBT): it must not despawn. */
    private boolean fromTemplate;

    public MilitiaEntity(EntityType<? extends MilitiaEntity> type, Level level, Faction faction) {
        super(type, level);
        this.faction = faction;
        this.xpReward = 8;
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 20.0D)
                .add(Attributes.MOVEMENT_SPEED, 0.27D)
                .add(Attributes.ATTACK_DAMAGE, 2.5D)
                .add(Attributes.FOLLOW_RANGE, 28.0D)
                .add(Attributes.KNOCKBACK_RESISTANCE, 0.1D);
    }

    /** Natural spawn rule (structure spawn overrides): no darkness needed, not on peaceful, configured chance. */
    public static boolean checkFighterSpawnRules(EntityType<MilitiaEntity> type, ServerLevelAccessor level,
                                                 MobSpawnType reason, BlockPos pos, RandomSource random) {
        if (level.getDifficulty() == Difficulty.PEACEFUL || !Mob.checkMobSpawnRules(type, level, reason, pos, random)) {
            return false;
        }
        return reason != MobSpawnType.NATURAL || random.nextDouble() < DonbassConfig.fighterSpawnChance();
    }

    // ----------------------------------------------------------- state ----
    @Override
    protected void defineSynchedData() {
        super.defineSynchedData();
        this.entityData.define(DATA_RANK, RANK_RECRUIT);
        this.entityData.define(DATA_STATE, STATE_IDLE);
    }

    public Faction getFaction() {
        return faction;
    }

    public int getRank() {
        return this.entityData.get(DATA_RANK);
    }

    public int getCombatState() {
        return this.entityData.get(DATA_STATE);
    }

    private void setCombatState(int state) {
        if (this.entityData.get(DATA_STATE) != state) {
            this.entityData.set(DATA_STATE, state);
        }
    }

    public boolean isHoldingRifle() {
        return this.getMainHandItem().getItem() instanceof AkRifleItem;
    }

    @Override
    public boolean isAlliedTo(Entity other) {
        if (other instanceof MilitiaEntity militia) {
            return !DonbassConfig.factionsFight() || militia.faction == this.faction;
        }
        return super.isAlliedTo(other);
    }

    // -------------------------------------------------------------- AI ----
    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(0, new FloatGoal(this));
        this.goalSelector.addGoal(1, new MilitiaRifleGoal(this));
        this.goalSelector.addGoal(2, new MilitiaFollowLeaderGoal(this, 1.0D));
        this.goalSelector.addGoal(3, new MoveTowardsRestrictionGoal(this, 0.9D));
        this.goalSelector.addGoal(4, new WaterAvoidingRandomStrollGoal(this, 0.8D));
        this.goalSelector.addGoal(5, new LookAtPlayerGoal(this, Player.class, 14.0F));
        this.goalSelector.addGoal(6, new RandomLookAroundGoal(this));
        // whoever hurts a fighter is attacked by the nearby squad mates (isAlliedTo keeps them off each other)
        this.targetSelector.addGoal(1, new HurtByTargetGoal(this).setAlertOthers());
        this.targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
        this.targetSelector.addGoal(3, new NearestAttackableTargetGoal<>(this, MilitiaEntity.class, 10, true, false,
                other -> DonbassConfig.factionsFight() && other instanceof MilitiaEntity m && m.faction != this.faction));
    }

    // --------------------------------------------------------- shooting ----
    private int magazineSize() {
        return getRank() == RANK_RECRUIT ? 20 : 30;
    }

    private double inaccuracyDegrees() {
        return switch (getRank()) {
            case RANK_SERGEANT -> 2.6D;
            case RANK_FIGHTER -> 3.6D;
            default -> 5.0D;
        };
    }

    private int aimDelay() {
        return switch (getRank()) {
            case RANK_SERGEANT -> 8;
            case RANK_FIGHTER -> 14;
            default -> 22;
        };
    }

    private int nextBurst() {
        return switch (getRank()) {
            case RANK_SERGEANT -> 4 + this.random.nextInt(3);
            case RANK_FIGHTER -> 3 + this.random.nextInt(3);
            default -> 2 + this.random.nextInt(2);
        };
    }

    private int restBetweenBursts() {
        return switch (getRank()) {
            case RANK_SERGEANT -> 16 + this.random.nextInt(14);
            case RANK_FIGHTER -> 24 + this.random.nextInt(20);
            default -> 34 + this.random.nextInt(26);
        };
    }

    /** Called every tick by MilitiaRifleGoal while a target is chosen. */
    public void tickCombat(LivingEntity target, boolean canSee, double distance) {
        if (firingDisplay > 0 && --firingDisplay == 0 && reloadTicks <= 0) {
            setCombatState(canSee ? STATE_AIMING : STATE_IDLE);
        }
        if (reloadTicks > 0) {
            setCombatState(STATE_RELOADING);
            if (--reloadTicks == 0) {
                ammo = magazineSize();
                setCombatState(STATE_AIMING);
            }
            return;
        }
        if (ammo <= 0) {
            reloadTicks = 55;
            aimTicks = 0;
            this.level().playSound(null, this.getX(), this.getY(), this.getZ(), ModSounds.AK_RELOAD.get(),
                    SoundSource.HOSTILE, 0.9F, 1.0F);
            return;
        }
        if (!canSee || distance > 30.0D) {
            aimTicks = 0;
            if (firingDisplay == 0) {
                setCombatState(STATE_IDLE);
            }
            return;
        }
        if (firingDisplay == 0) {
            setCombatState(STATE_AIMING);
        }
        if (pause > 0) {
            pause--;
            return;
        }
        if (aimTicks < aimDelay()) {
            aimTicks++;
            return;
        }
        if (betweenShots > 0) {
            betweenShots--;
            return;
        }
        if (burstLeft <= 0) {
            burstLeft = nextBurst();
        }
        fire(target, distance);
        burstLeft--;
        betweenShots = 3;
        if (burstLeft <= 0) {
            pause = restBetweenBursts();
        }
    }

    private void fire(LivingEntity target, double distance) {
        ammo--;
        Vec3 origin = this.getEyePosition().add(0.0D, -0.25D, 0.0D);
        Vec3 aimAt = target.getBoundingBox().getCenter();
        Vec3 dir = aimAt.subtract(origin).normalize();
        // the further the target, the wider the cone
        double degrees = inaccuracyDegrees() * (0.7D + Math.min(distance, 30.0D) / 30.0D);
        dir = Ballistics.spread(this.random, dir, degrees);
        float damage = (float) (this.getAttributeValue(Attributes.ATTACK_DAMAGE) * DonbassConfig.fighterDamageMultiplier()
                * difficultyFactor());
        Ballistics.shoot(this.level(), this, origin, dir, 40.0D, damage, e -> e != this && !e.isSpectator()
                && e.isPickable() && !(e instanceof MilitiaEntity m && m.faction == this.faction)
                && !(e instanceof ItemEntity));
        this.level().playSound(null, this.getX(), this.getY(), this.getZ(), ModSounds.AK_SHOT.get(),
                SoundSource.HOSTILE, 1.1F, 0.9F + this.random.nextFloat() * 0.15F);
        firingDisplay = 3;
        setCombatState(STATE_FIRING);
    }

    private float difficultyFactor() {
        return switch (this.level().getDifficulty()) {
            case EASY -> 0.7F;
            case HARD -> 1.25F;
            default -> 1.0F;
        };
    }

    @Override
    public void aiStep() {
        super.aiStep();
        if (!this.level().isClientSide && !initialized) {
            setUp(this.level().getCurrentDifficultyAt(this.blockPosition()), fromTemplate);
        }
        if (!this.level().isClientSide && this.getTarget() == null && getCombatState() != STATE_IDLE) {
            setCombatState(STATE_IDLE);
            aimTicks = 0;
        }
    }

    // ----------------------------------------------------- equipment/rank ----
    @Nullable
    @Override
    public SpawnGroupData finalizeSpawn(ServerLevelAccessor level, DifficultyInstance difficulty, MobSpawnType reason,
                                        @Nullable SpawnGroupData spawnData, @Nullable CompoundTag tag) {
        SpawnGroupData data = super.finalizeSpawn(level, difficulty, reason, spawnData, tag);
        setUp(difficulty, fromTemplate || reason == MobSpawnType.STRUCTURE || (tag != null && tag.contains("Rank")));
        return data;
    }

    /**
     * Picks the rank (unless it was preset in the NBT, as structure templates do), applies it, equips the fighter
     * and sets its patrol area. Runs once: from finalizeSpawn, or from aiStep for entities created without it.
     */
    private void setUp(DifficultyInstance difficulty, boolean placedByStructure) {
        if (initialized) {
            return;
        }
        initialized = true;
        int rank;
        if (placedByStructure) {
            this.setPersistenceRequired();                  // the garrison of a blockpost does not despawn
        }
        if (fromTemplate) {
            rank = getRank();
        } else {
            float roll = this.random.nextFloat();
            float sergeantChance = 0.12F + difficulty.getEffectiveDifficulty() * 0.03F;
            rank = roll < sergeantChance ? RANK_SERGEANT : roll < 0.5F ? RANK_FIGHTER : RANK_RECRUIT;
        }
        applyRank(rank);
        this.populateDefaultEquipmentSlots(this.random, difficulty);
        if (!this.hasRestriction()) {
            this.restrictTo(this.blockPosition(), 18);
        }
    }

    /** Sets the attributes of a rank and refills health. */
    private void applyRank(int rank) {
        this.entityData.set(DATA_RANK, rank);
        double health = rank == RANK_SERGEANT ? 26.0D : rank == RANK_FIGHTER ? 20.0D : 16.0D;
        double damage = rank == RANK_SERGEANT ? 3.0D : rank == RANK_FIGHTER ? 2.5D : 2.0D;
        double speed = rank == RANK_SERGEANT ? 0.28D : rank == RANK_FIGHTER ? 0.27D : 0.26D;
        this.getAttribute(Attributes.MAX_HEALTH).setBaseValue(health);
        this.getAttribute(Attributes.ATTACK_DAMAGE).setBaseValue(damage);
        this.getAttribute(Attributes.MOVEMENT_SPEED).setBaseValue(speed);
        this.setHealth((float) health);
        this.ammo = magazineSize();
        this.xpReward = 6 + rank * 4;
    }

    /** Piece 0..3 (helmet, jacket, trousers, boots) of the uniform of the given squad. */
    private static ItemStack uniformPiece(Faction faction, int index) {
        Item item = faction == Faction.NORTH
                ? switch (index) {
                    case 0 -> ModItems.STEPPE_HELMET.get();
                    case 1 -> ModItems.STEPPE_JACKET.get();
                    case 2 -> ModItems.STEPPE_TROUSERS.get();
                    default -> ModItems.STEPPE_BOOTS.get();
                }
                : switch (index) {
                    case 0 -> ModItems.TERRICONE_HELMET.get();
                    case 1 -> ModItems.TERRICONE_JACKET.get();
                    case 2 -> ModItems.TERRICONE_TROUSERS.get();
                    default -> ModItems.TERRICONE_BOOTS.get();
                };
        return new ItemStack(item);
    }

    private static final EquipmentSlot[] SLOTS = {EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.LEGS, EquipmentSlot.FEET};

    @Override
    protected void populateDefaultEquipmentSlots(RandomSource random, DifficultyInstance difficulty) {
        int rank = getRank();
        // chance to wear each piece: helmet, jacket, trousers, boots
        float[] chance = switch (rank) {
            case RANK_SERGEANT -> new float[] {1.0F, 1.0F, 0.85F, 0.85F};
            case RANK_FIGHTER -> new float[] {0.85F, 0.7F, 0.45F, 0.6F};
            default -> new float[] {0.25F, 0.35F, 0.25F, 0.35F};
        };
        float armorDrop = rank == RANK_SERGEANT ? 0.12F : rank == RANK_FIGHTER ? 0.08F : 0.05F;
        for (int i = 0; i < SLOTS.length; i++) {
            if (random.nextFloat() < chance[i]) {
                this.setItemSlot(SLOTS[i], uniformPiece(faction, i));
                this.setDropChance(SLOTS[i], armorDrop);
            }
        }
        if (rank == RANK_SERGEANT && random.nextFloat() < 0.2F) {      // a few sergeants wear a coal chestplate
            this.setItemSlot(EquipmentSlot.CHEST, new ItemStack(ModItems.COAL_CHESTPLATE.get()));
            this.setDropChance(EquipmentSlot.CHEST, 0.15F);
        }
        ItemStack rifle = new ItemStack(ModItems.AK_RIFLE.get());
        AkRifleItem.setAmmo(rifle, random.nextInt(magazineSize() + 1));
        this.setItemSlot(EquipmentSlot.MAINHAND, rifle);
        // rifle drop chance per rank: rarer than the ammunition in the loot table
        this.setDropChance(EquipmentSlot.MAINHAND, rank == RANK_SERGEANT ? 0.18F : rank == RANK_FIGHTER ? 0.10F : 0.04F);
    }

    // ------------------------------------------------------------ sounds ----
    @Override
    protected SoundEvent getAmbientSound() {
        return ModSounds.MILITIA_AMBIENT.get();
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return ModSounds.MILITIA_HURT.get();
    }

    @Override
    protected SoundEvent getDeathSound() {
        return ModSounds.MILITIA_DEATH.get();
    }

    // --------------------------------------------------------------- NBT ----
    @Override
    public void addAdditionalSaveData(CompoundTag tag) {
        super.addAdditionalSaveData(tag);
        tag.putInt("Rank", getRank());
        tag.putInt("Ammo", ammo);
        tag.putBoolean("SetUp", initialized);
        if (this.hasRestriction()) {
            BlockPos home = this.getRestrictCenter();
            tag.putInt("HomeX", home.getX());
            tag.putInt("HomeY", home.getY());
            tag.putInt("HomeZ", home.getZ());
        }
    }

    @Override
    public void readAdditionalSaveData(CompoundTag tag) {
        super.readAdditionalSaveData(tag);
        if (tag.contains("Rank")) {
            this.fromTemplate = !tag.getBoolean("SetUp");   // a preset rank of a template entity, not yet set up
            // health and attribute values are restored by LivingEntity; only the synced rank is ours
            this.entityData.set(DATA_RANK, Math.max(0, Math.min(2, tag.getInt("Rank"))));
        }
        if (tag.contains("Ammo")) {
            this.ammo = tag.getInt("Ammo");
        }
        this.initialized = tag.getBoolean("SetUp");
        if (tag.contains("HomeX")) {
            this.restrictTo(new BlockPos(tag.getInt("HomeX"), tag.getInt("HomeY"), tag.getInt("HomeZ")), 18);
        }
    }
}

package com.donbass.mod.entity;

import com.donbass.mod.config.DonbassConfig;
import com.donbass.mod.entity.ai.MinerRestGoal;
import com.donbass.mod.entity.ai.MinerSleepGoal;
import com.donbass.mod.entity.ai.MinerWorkGoal;
import com.donbass.mod.registry.ModItems;
import com.donbass.mod.registry.ModSounds;
import javax.annotation.Nullable;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.stats.Stats;
import net.minecraft.util.RandomSource;
import net.minecraft.world.DifficultyInstance;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.AgeableMob;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.ExperienceOrb;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.entity.SpawnGroupData;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.LookAtTradingPlayerGoal;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.MoveTowardsRestrictionGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.TradeWithPlayerGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.navigation.GroundPathNavigation;
import net.minecraft.world.entity.npc.AbstractVillager;
import net.minecraft.world.entity.npc.VillagerData;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.trading.MerchantOffer;
import net.minecraft.world.item.trading.MerchantOffers;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.ServerLevelAccessor;

/**
 * A neutral miner NPC that trades like a villager (five levels, XP bar) but with its own table (MinerTrades).
 * It works at coal/furnace blocks by day, sleeps in beds at night and rests now and then. If it is hurt it
 * fights back with its pickaxe and the miners nearby join in.
 */
public class MinerEntity extends AbstractVillager {
    private static final int MAX_LEVEL = 5;
    /** How many of the listed offers of a level are given to one miner (level 1..5). */
    private static final int[] OFFERS_PER_LEVEL = {4, 5, 6, 7, 6};

    private int minerLevel = 1;
    private int minerXp;
    private int restockTimer;
    private boolean levelUpPending;
    private boolean initialized;

    public MinerEntity(EntityType<? extends MinerEntity> type, Level level) {
        super(type, level);
        ((GroundPathNavigation) this.getNavigation()).setCanOpenDoors(true);
        this.getNavigation().setCanFloat(true);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Mob.createMobAttributes()
                .add(Attributes.MAX_HEALTH, 24.0D)
                .add(Attributes.MOVEMENT_SPEED, 0.5D)
                .add(Attributes.ATTACK_DAMAGE, 2.0D)
                .add(Attributes.FOLLOW_RANGE, 24.0D);
    }

    /** Natural spawn rule (structure spawn overrides): solid ground plus the configured chance. */
    public static boolean checkMinerSpawnRules(EntityType<MinerEntity> type, ServerLevelAccessor level,
                                               MobSpawnType reason, BlockPos pos, RandomSource random) {
        if (!Mob.checkMobSpawnRules(type, level, reason, pos, random)) {
            return false;
        }
        return reason != MobSpawnType.NATURAL || random.nextDouble() < DonbassConfig.minerSpawnChance();
    }

    // ------------------------------------------------------------- AI ----
    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(0, new FloatGoal(this));
        this.goalSelector.addGoal(1, new TradeWithPlayerGoal(this));
        this.goalSelector.addGoal(1, new LookAtTradingPlayerGoal(this));
        this.goalSelector.addGoal(2, new MinerSleepGoal(this));
        this.goalSelector.addGoal(3, new MeleeAttackGoal(this, 1.15D, false));
        this.goalSelector.addGoal(4, new MinerWorkGoal(this, 0.6D));
        this.goalSelector.addGoal(5, new MinerRestGoal(this));
        this.goalSelector.addGoal(6, new MoveTowardsRestrictionGoal(this, 0.55D));
        this.goalSelector.addGoal(7, new WaterAvoidingRandomStrollGoal(this, 0.55D));
        this.goalSelector.addGoal(8, new LookAtPlayerGoal(this, Player.class, 6.0F));
        this.goalSelector.addGoal(9, new RandomLookAroundGoal(this));
        // retaliate against whoever hurt this miner; every miner nearby joins in
        this.targetSelector.addGoal(1, new HurtByTargetGoal(this).setAlertOthers());
    }

    public int getMinerLevel() {
        return minerLevel;
    }

    @Override
    public SpawnGroupData finalizeSpawn(ServerLevelAccessor level, DifficultyInstance difficulty, MobSpawnType reason,
                                        @Nullable SpawnGroupData spawnData, @Nullable CompoundTag tag) {
        // AgeableMob would make 5% of the miners babies: hand it group data that never spawns babies
        SpawnGroupData group = spawnData instanceof AgeableMob.AgeableMobGroupData ? spawnData
                : new AgeableMob.AgeableMobGroupData(false);
        SpawnGroupData data = super.finalizeSpawn(level, difficulty, reason, group, tag);
        setUp();
        return data;
    }

    /** Level, pickaxe and home area; runs once (finalizeSpawn, or the first AI tick for entities created without it). */
    private void setUp() {
        if (initialized) {
            return;
        }
        initialized = true;
        int roll = this.random.nextInt(10);
        this.minerLevel = roll < 6 ? 1 : roll < 9 ? 2 : 3;
        this.minerXp = VillagerData.getMinXpPerLevel(this.minerLevel);
        this.setItemSlot(EquipmentSlot.MAINHAND, new ItemStack(ModItems.MINERS_PICKAXE.get()));
        this.setDropChance(EquipmentSlot.MAINHAND, 0.0F);
        if (!this.hasRestriction()) {
            this.restrictTo(this.blockPosition(), 28);
        }
    }

    // ---------------------------------------------------------- trading ----
    @Override
    public InteractionResult mobInteract(Player player, InteractionHand hand) {
        ItemStack held = player.getItemInHand(hand);
        if (held.is(Items.VILLAGER_SPAWN_EGG) || !this.isAlive() || this.isTrading() || this.isBaby()) {
            return super.mobInteract(player, hand);
        }
        if (this.getTarget() != null) {
            if (!this.level().isClientSide) {
                player.displayClientMessage(Component.translatable("message.donbass.miner_hostile"), true);
                this.setUnhappyCounter(40);
                this.playSound(ModSounds.MINER_NO.get(), this.getSoundVolume(), this.getVoicePitch());
            }
            return InteractionResult.sidedSuccess(this.level().isClientSide);
        }
        if (hand == InteractionHand.MAIN_HAND) {
            player.awardStat(Stats.TALKED_TO_VILLAGER);
        }
        if (this.getOffers().isEmpty()) {
            return InteractionResult.sidedSuccess(this.level().isClientSide);
        }
        if (!this.level().isClientSide) {
            if (this.isSleeping()) {
                this.stopSleeping();
            }
            this.setTradingPlayer(player);
            this.openTradingScreen(player, this.getDisplayName(), this.minerLevel);
        }
        return InteractionResult.sidedSuccess(this.level().isClientSide);
    }

    @Override
    protected void updateTrades() {
        setUp();                                  // the level must be decided before the first trades are rolled
        MerchantOffers offers = this.getOffers();
        for (int lvl = 1; lvl <= this.minerLevel; lvl++) {
            addTradesForLevel(offers, lvl);
        }
    }

    private void addTradesForLevel(MerchantOffers offers, int lvl) {
        this.addOffersFromItemListings(offers, MinerTrades.LEVELS[lvl - 1], OFFERS_PER_LEVEL[lvl - 1]);
    }

    @Override
    protected void rewardTradeXp(MerchantOffer offer) {
        if (offer.shouldRewardExp()) {
            int amount = 3 + this.random.nextInt(4);
            this.level().addFreshEntity(new ExperienceOrb(this.level(), this.getX(), this.getY() + 0.5D, this.getZ(), amount));
        }
        this.minerXp += offer.getXp();
        if (this.minerLevel < MAX_LEVEL && VillagerData.canLevelUp(this.minerLevel)
                && this.minerXp >= VillagerData.getMaxXpPerLevel(this.minerLevel)) {
            this.levelUpPending = true;           // applied after the trading screen is closed
        }
    }

    @Override
    protected void customServerAiStep() {
        super.customServerAiStep();
        if (!this.initialized) {
            setUp();
        }
        if (!this.isTrading()) {
            if (this.levelUpPending) {
                this.levelUpPending = false;
                this.minerLevel++;
                addTradesForLevel(this.getOffers(), this.minerLevel);
                if (this.level() instanceof ServerLevel serverLevel) {
                    serverLevel.sendParticles(ParticleTypes.HAPPY_VILLAGER, this.getX(), this.getY() + 1.0D,
                            this.getZ(), 7, 0.5D, 0.5D, 0.5D, 0.02D);
                }
                this.playSound(ModSounds.MINER_YES.get(), this.getSoundVolume(), this.getVoicePitch());
            }
            if (++this.restockTimer >= DonbassConfig.minerRestockTicks()) {
                this.restockTimer = 0;
                for (MerchantOffer offer : this.getOffers()) {
                    offer.resetUses();
                }
            }
        }
    }

    @Override
    public int getVillagerXp() {
        return this.minerXp;
    }

    @Override
    public void overrideXp(int xp) {
        this.minerXp = xp;
    }

    @Override
    public boolean showProgressBar() {
        return true;
    }

    @Override
    public boolean removeWhenFarAway(double distanceToClosestPlayer) {
        return false;
    }

    @Nullable
    @Override
    public AgeableMob getBreedOffspring(ServerLevel level, AgeableMob partner) {
        return null;
    }

    // ----------------------------------------------------------- sounds ----
    @Override
    protected SoundEvent getAmbientSound() {
        return this.isTrading() ? ModSounds.MINER_YES.get() : ModSounds.MINER_AMBIENT.get();
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return ModSounds.MINER_HURT.get();
    }

    @Override
    protected SoundEvent getDeathSound() {
        return ModSounds.MINER_DEATH.get();
    }

    @Override
    public SoundEvent getNotifyTradeSound() {
        return ModSounds.MINER_YES.get();
    }

    @Override
    protected SoundEvent getTradeUpdatedSound(boolean empty) {
        return empty ? ModSounds.MINER_NO.get() : ModSounds.MINER_YES.get();
    }

    // -------------------------------------------------------------- NBT ----
    @Override
    public void addAdditionalSaveData(CompoundTag tag) {
        super.addAdditionalSaveData(tag);
        tag.putInt("MinerLevel", this.minerLevel);
        tag.putInt("MinerXp", this.minerXp);
        tag.putBoolean("SetUp", this.initialized);
        tag.putInt("RestockTimer", this.restockTimer);
        BlockPos home = this.getRestrictCenter();
        if (this.hasRestriction()) {
            tag.putInt("HomeX", home.getX());
            tag.putInt("HomeY", home.getY());
            tag.putInt("HomeZ", home.getZ());
        }
    }

    @Override
    public void readAdditionalSaveData(CompoundTag tag) {
        super.readAdditionalSaveData(tag);
        if (tag.contains("MinerLevel")) {
            this.minerLevel = Math.max(1, Math.min(MAX_LEVEL, tag.getInt("MinerLevel")));
        }
        this.minerXp = tag.getInt("MinerXp");
        this.initialized = tag.getBoolean("SetUp");
        this.restockTimer = tag.getInt("RestockTimer");
        if (tag.contains("HomeX")) {
            this.restrictTo(new BlockPos(tag.getInt("HomeX"), tag.getInt("HomeY"), tag.getInt("HomeZ")), 28);
        }
    }
}

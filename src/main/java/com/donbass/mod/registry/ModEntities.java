package com.donbass.mod.registry;

import com.donbass.mod.DonbassMod;
import com.donbass.mod.entity.CombineDirectorEntity;
import com.donbass.mod.entity.MilitiaEntity;
import com.donbass.mod.entity.MinerEntity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

public final class ModEntities {
    public static final DeferredRegister<EntityType<?>> ENTITIES =
            DeferredRegister.create(ForgeRegistries.ENTITY_TYPES, DonbassMod.MOD_ID);

    public static final RegistryObject<EntityType<MinerEntity>> MINER = ENTITIES.register("miner",
            () -> EntityType.Builder.<MinerEntity>of(MinerEntity::new, MobCategory.CREATURE)
                    .sized(0.6F, 1.95F).clientTrackingRange(10)
                    .build(DonbassMod.MOD_ID + ":miner"));

    public static final RegistryObject<EntityType<MilitiaEntity>> NORTH_FIGHTER = ENTITIES.register("north_fighter",
            () -> EntityType.Builder.<MilitiaEntity>of(
                            (type, level) -> new MilitiaEntity(type, level, MilitiaEntity.Faction.NORTH),
                            MobCategory.MONSTER)
                    .sized(0.6F, 1.95F).clientTrackingRange(8)
                    .build(DonbassMod.MOD_ID + ":north_fighter"));

    public static final RegistryObject<EntityType<MilitiaEntity>> SOUTH_FIGHTER = ENTITIES.register("south_fighter",
            () -> EntityType.Builder.<MilitiaEntity>of(
                            (type, level) -> new MilitiaEntity(type, level, MilitiaEntity.Faction.SOUTH),
                            MobCategory.MONSTER)
                    .sized(0.6F, 1.95F).clientTrackingRange(8)
                    .build(DonbassMod.MOD_ID + ":south_fighter"));

    /** The boss. Never spawns naturally: it is only called with the siren (CombineSirenItem). */
    public static final RegistryObject<EntityType<CombineDirectorEntity>> COMBINE_DIRECTOR =
            ENTITIES.register("combine_director",
                    () -> EntityType.Builder.<CombineDirectorEntity>of(CombineDirectorEntity::new, MobCategory.MONSTER)
                            .sized(0.75F, 2.45F).clientTrackingRange(12).fireImmune()
                            .build(DonbassMod.MOD_ID + ":combine_director"));

    private ModEntities() {}
}

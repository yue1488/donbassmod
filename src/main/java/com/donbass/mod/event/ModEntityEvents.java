package com.donbass.mod.event;

import com.donbass.mod.DonbassMod;
import com.donbass.mod.entity.CombineDirectorEntity;
import com.donbass.mod.entity.MilitiaEntity;
import com.donbass.mod.entity.MinerEntity;
import com.donbass.mod.registry.ModEntities;
import net.minecraft.world.entity.SpawnPlacements;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraftforge.event.entity.EntityAttributeCreationEvent;
import net.minecraftforge.event.entity.SpawnPlacementRegisterEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

/** Mod-bus events: entity attributes and spawn rules. */
@Mod.EventBusSubscriber(modid = DonbassMod.MOD_ID, bus = Mod.EventBusSubscriber.Bus.MOD)
public final class ModEntityEvents {
    private ModEntityEvents() {}

    @SubscribeEvent
    public static void onAttributes(EntityAttributeCreationEvent event) {
        event.put(ModEntities.MINER.get(), MinerEntity.createAttributes().build());
        event.put(ModEntities.NORTH_FIGHTER.get(), MilitiaEntity.createAttributes().build());
        event.put(ModEntities.SOUTH_FIGHTER.get(), MilitiaEntity.createAttributes().build());
        event.put(ModEntities.COMBINE_DIRECTOR.get(), CombineDirectorEntity.createAttributes().build());
    }

    @SubscribeEvent
    public static void onSpawnPlacements(SpawnPlacementRegisterEvent event) {
        event.register(ModEntities.MINER.get(), SpawnPlacements.Type.ON_GROUND,
                Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, MinerEntity::checkMinerSpawnRules,
                SpawnPlacementRegisterEvent.Operation.OR);
        event.register(ModEntities.NORTH_FIGHTER.get(), SpawnPlacements.Type.ON_GROUND,
                Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, MilitiaEntity::checkFighterSpawnRules,
                SpawnPlacementRegisterEvent.Operation.OR);
        event.register(ModEntities.SOUTH_FIGHTER.get(), SpawnPlacements.Type.ON_GROUND,
                Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, MilitiaEntity::checkFighterSpawnRules,
                SpawnPlacementRegisterEvent.Operation.OR);
    }
}

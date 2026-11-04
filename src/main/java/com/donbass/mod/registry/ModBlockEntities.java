package com.donbass.mod.registry;

import com.donbass.mod.DonbassMod;
import com.donbass.mod.block.WeaponWorkbenchBlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

public final class ModBlockEntities {
    public static final DeferredRegister<BlockEntityType<?>> BLOCK_ENTITIES =
            DeferredRegister.create(ForgeRegistries.BLOCK_ENTITY_TYPES, DonbassMod.MOD_ID);

    public static final RegistryObject<BlockEntityType<WeaponWorkbenchBlockEntity>> WEAPON_WORKBENCH =
            BLOCK_ENTITIES.register("weapon_workbench",
                    () -> BlockEntityType.Builder.of(WeaponWorkbenchBlockEntity::new,
                            ModBlocks.WEAPON_WORKBENCH.get()).build(null));

    private ModBlockEntities() {}
}

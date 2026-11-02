package com.donbass.mod.registry;

import com.donbass.mod.DonbassMod;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.tags.TagKey;
import net.minecraft.world.level.block.Block;

public final class ModTags {
    /** Blocks the miners walk to and "work" at (data/donbass/tags/blocks/miner_workstations.json). */
    public static final TagKey<Block> MINER_WORKSTATIONS =
            TagKey.create(Registries.BLOCK, new ResourceLocation(DonbassMod.MOD_ID, "miner_workstations"));

    private ModTags() {}
}

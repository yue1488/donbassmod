package com.donbass.mod.worldgen;

import com.donbass.mod.registry.ModBlocks;
import com.mojang.serialization.Codec;
import net.minecraft.core.BlockPos;
import net.minecraft.tags.BlockTags;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.feature.Feature;
import net.minecraft.world.level.levelgen.feature.FeaturePlaceContext;
import net.minecraft.world.level.levelgen.feature.configurations.NoneFeatureConfiguration;

/**
 * A coal seam: a thin, slightly tilted lens of coal that replaces stone over a wide area,
 * unlike an ordinary blob-shaped ore vein. Deep parts of a seam may contain anthracite.
 * The horizontal radius is capped at 9 so the lens always stays inside the 3x3 chunk
 * region available to features during world generation.
 */
public class CoalSeamFeature extends Feature<NoneFeatureConfiguration> {
    private static final int MIN_RADIUS = 4;
    private static final int RADIUS_SPREAD = 6; // radius is 4..9

    public CoalSeamFeature(Codec<NoneFeatureConfiguration> codec) {
        super(codec);
    }

    @Override
    public boolean place(FeaturePlaceContext<NoneFeatureConfiguration> context) {
        WorldGenLevel level = context.level();
        RandomSource random = context.random();
        BlockPos origin = context.origin();

        int radiusX = MIN_RADIUS + random.nextInt(RADIUS_SPREAD);
        int radiusZ = MIN_RADIUS + random.nextInt(RADIUS_SPREAD);
        int thickness = 1 + random.nextInt(3); // 1..3 blocks
        double slopeX = (random.nextDouble() - 0.5D) * 0.35D;
        double slopeZ = (random.nextDouble() - 0.5D) * 0.35D;

        BlockState coal = ModBlocks.COAL_SEAM.get().defaultBlockState();
        BlockState anthracite = ModBlocks.ANTHRACITE_ORE.get().defaultBlockState();
        BlockState deepAnthracite = ModBlocks.DEEPSLATE_ANTHRACITE_ORE.get().defaultBlockState();

        boolean placedAny = false;
        BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();

        for (int dx = -radiusX; dx <= radiusX; dx++) {
            for (int dz = -radiusZ; dz <= radiusZ; dz++) {
                double distance = (double) (dx * dx) / (radiusX * radiusX) + (double) (dz * dz) / (radiusZ * radiusZ);
                if (distance > 1.0D) {
                    continue;
                }
                // The seam gets thinner towards its edges and has ragged borders.
                int layers = thickness - (distance > 0.55D ? 1 : 0);
                if (distance > 0.85D && random.nextInt(3) == 0) {
                    layers--;
                }
                if (layers <= 0) {
                    continue;
                }
                int baseY = origin.getY() + (int) Math.round(dx * slopeX + dz * slopeZ);
                for (int layer = 0; layer < layers; layer++) {
                    pos.set(origin.getX() + dx, baseY + layer, origin.getZ() + dz);
                    BlockState existing = level.getBlockState(pos);
                    if (!existing.is(BlockTags.BASE_STONE_OVERWORLD)) {
                        continue;
                    }
                    BlockState state = coal;
                    if (pos.getY() < 16 && random.nextFloat() < 0.15F) {
                        state = existing.is(Blocks.DEEPSLATE) ? deepAnthracite : anthracite;
                    }
                    if (level.setBlock(pos, state, 2)) {
                        placedAny = true;
                    }
                }
            }
        }
        return placedAny;
    }
}

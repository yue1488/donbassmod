package com.donbass.mod.worldgen;

import com.donbass.mod.registry.ModBlocks;
import com.mojang.serialization.Codec;
import net.minecraft.core.BlockPos;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.feature.Feature;
import net.minecraft.world.level.levelgen.feature.FeaturePlaceContext;
import net.minecraft.world.level.levelgen.feature.configurations.NoneFeatureConfiguration;

/**
 * A terricone: a steep, flat-topped heap of mine spoil piled on top of the terrain.
 * Old heaps are burnt red, young ones are dark, and the upper part may still be smouldering.
 * The radius is capped at 14 so the heap always stays inside the 3x3 chunk area that features
 * may touch during world generation.
 */
public class TerriconeFeature extends Feature<NoneFeatureConfiguration> {
    private static final int MIN_RADIUS = 7;
    private static final int RADIUS_SPREAD = 8; // radius is 7..14

    public TerriconeFeature(Codec<NoneFeatureConfiguration> codec) {
        super(codec);
    }

    @Override
    public boolean place(FeaturePlaceContext<NoneFeatureConfiguration> context) {
        WorldGenLevel level = context.level();
        RandomSource random = context.random();
        BlockPos origin = context.origin();

        int baseY = level.getHeight(Heightmap.Types.WORLD_SURFACE_WG, origin.getX(), origin.getZ());
        if (baseY <= context.chunkGenerator().getSeaLevel()) {
            return false; // never build heaps in lakes
        }

        int radius = MIN_RADIUS + random.nextInt(RADIUS_SPREAD);
        int height = (int) (radius * (0.9D + random.nextDouble() * 0.5D));
        boolean burnt = random.nextFloat() < 0.45F; // an old, burnt-out heap
        boolean burning = !burnt && random.nextFloat() < 0.5F; // a young heap that still smoulders

        BlockState rock = ModBlocks.SPOIL_ROCK.get().defaultBlockState();
        BlockState burntRock = ModBlocks.BURNT_SPOIL.get().defaultBlockState();
        BlockState gravel = ModBlocks.SPOIL_GRAVEL.get().defaultBlockState();
        BlockState shale = ModBlocks.COAL_SHALE.get().defaultBlockState();
        BlockState embers = ModBlocks.SMOLDERING_SPOIL.get().defaultBlockState();

        boolean placedAny = false;
        BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();

        for (int dx = -radius; dx <= radius; dx++) {
            for (int dz = -radius; dz <= radius; dz++) {
                double dist = Math.sqrt(dx * dx + dz * dz);
                if (dist > radius) {
                    continue;
                }
                int x = origin.getX() + dx;
                int z = origin.getZ() + dz;
                double profile = Math.pow(1.0D - dist / radius, 0.85D);
                int top = baseY + (int) Math.round(height * profile + random.nextFloat() - 0.5F);
                top = Math.min(top, baseY + height - 1); // flat top
                int groundY = level.getHeight(Heightmap.Types.WORLD_SURFACE_WG, x, z);

                for (int y = groundY; y <= top; y++) {
                    pos.set(x, y, z);
                    // pile only onto free space: never overwrite solid terrain, and never displace water
                    if (level.getBlockState(pos).isSolid() || !level.getFluidState(pos).isEmpty()) {
                        continue;
                    }
                    int depth = top - y; // 0 = outer shell of the heap
                    BlockState state = rock;
                    if (depth <= 1) {
                        float roll = random.nextFloat();
                        if (burnt) {
                            state = roll < 0.65F ? burntRock : roll < 0.85F ? rock : gravel;
                        } else if (burning && y > baseY + height * 0.55D && roll < 0.14F) {
                            state = embers;
                        } else if (roll < 0.22F) {
                            state = gravel;
                        } else if (roll < 0.34F) {
                            state = shale;
                        }
                    } else if (random.nextFloat() < 0.07F) {
                        state = shale;
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

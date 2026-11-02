package com.donbass.mod.entity;

import com.donbass.mod.registry.ModBlocks;
import com.donbass.mod.registry.ModItems;
import java.util.function.Supplier;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.npc.VillagerTrades;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.trading.MerchantOffer;
import net.minecraft.world.level.ItemLike;

/**
 * Trade tables of the miners, five levels. The currency is the miner's token (donbass:miners_token).
 * Common goods are bought and sold at level 1; rarer equipment unlocks with the level, and the
 * coal armour is only sold by master miners (level 5).
 */
public final class MinerTrades {
    private MinerTrades() {}

    /** Offers added when a miner reaches (or starts at) a level: index 0 = level 1. */
    public static final VillagerTrades.ItemListing[][] LEVELS = {
            { // level 1: a labourer - trades in coal and scrap, sells food and torches
                    buys(() -> Items.COAL, 16, 2, 16, 2),
                    buys(ModItems.IRON_SCRAP::get, 6, 1, 16, 2),
                    buys(ModItems.COAL_DUST::get, 8, 1, 12, 2),
                    sells(1, ModItems.MINERS_RATION::get, 2, 16, 2),
                    sells(1, () -> Items.TORCH, 8, 16, 2),
                    sells(2, () -> Items.COAL_BLOCK, 1, 8, 3)},
            { // level 2: a face worker - raw iron, the first tools and the lamp
                    buys(() -> Items.RAW_IRON, 8, 2, 12, 5),
                    buys(() -> Items.IRON_INGOT, 3, 2, 12, 5),
                    buys(() -> Items.RAW_COPPER, 6, 1, 12, 5),
                    sells(5, ModItems.MINERS_PICKAXE::get, 1, 4, 6),
                    sells(4, ModItems.MINERS_HELMET::get, 1, 4, 6),
                    sells(4, ModItems.MINERS_BOOTS::get, 1, 4, 6),
                    sells(2, ModBlocks.MINE_LAMP::get, 1, 8, 5)},
            { // level 3: a brigadier - anthracite, coke, clothes and mine equipment
                    buys(ModItems.ANTHRACITE::get, 6, 3, 12, 9),
                    buys(ModItems.COKE::get, 8, 3, 12, 9),
                    buys(() -> Items.GOLD_INGOT, 2, 4, 8, 9),
                    sells(6, ModItems.MINERS_JACKET::get, 1, 4, 10),
                    sells(5, ModItems.MINERS_TROUSERS::get, 1, 4, 10),
                    sells(3, ModBlocks.VENTILATION_GRATE::get, 2, 8, 9),
                    sells(6, ModBlocks.COAL_BUNKER::get, 1, 4, 10),
                    sells(4, () -> Items.POWERED_RAIL, 6, 8, 9),
                    sells(5, ModItems.DONBASS_TICKET::get, 1, 4, 10)},
            { // level 4: a foreman - redstone, parts, ammunition and blasting charges
                    buys(() -> Items.REDSTONE, 8, 2, 12, 14),
                    buys(ModBlocks.ANTHRACITE_BLOCK::get, 1, 5, 6, 14),
                    sells(6, ModItems.RIFLE_CARTRIDGE::get, 8, 8, 14),
                    sells(8, ModItems.GUN_PARTS::get, 1, 4, 15),
                    sells(10, ModItems.RIFLE_MAGAZINE::get, 1, 3, 15),
                    sells(8, ModItems.COAL_PLATE::get, 2, 6, 14),
                    sells(12, () -> Items.TNT, 2, 6, 14)},
            { // level 5: a master - diamonds for tokens, and the coal armour
                    buys(() -> Items.DIAMOND, 3, 12, 6, 20),
                    buys(() -> Items.EMERALD, 4, 8, 6, 20),
                    sells(14, ModItems.COAL_HELMET::get, 1, 2, 25),
                    sells(22, ModItems.COAL_CHESTPLATE::get, 1, 2, 30),
                    sells(19, ModItems.COAL_LEGGINGS::get, 1, 2, 28),
                    sells(11, ModItems.COAL_BOOTS::get, 1, 2, 24)}
    };

    /** The miner takes 'count' of an item and pays 'tokens'. */
    private static VillagerTrades.ItemListing buys(Supplier<? extends ItemLike> item, int count, int tokens,
                                                   int maxUses, int xp) {
        return new Trade(item, count, ModItems.MINERS_TOKEN::get, tokens, maxUses, xp);
    }

    /** The miner takes 'tokens' and hands out 'count' of an item. */
    private static VillagerTrades.ItemListing sells(int tokens, Supplier<? extends ItemLike> item, int count,
                                                    int maxUses, int xp) {
        return new Trade(ModItems.MINERS_TOKEN::get, tokens, item, count, maxUses, xp);
    }

    private static final class Trade implements VillagerTrades.ItemListing {
        private final Supplier<? extends ItemLike> cost;
        private final int costCount;
        private final Supplier<? extends ItemLike> result;
        private final int resultCount;
        private final int maxUses;
        private final int xp;

        private Trade(Supplier<? extends ItemLike> cost, int costCount, Supplier<? extends ItemLike> result,
                      int resultCount, int maxUses, int xp) {
            this.cost = cost;
            this.costCount = costCount;
            this.result = result;
            this.resultCount = resultCount;
            this.maxUses = maxUses;
            this.xp = xp;
        }

        @Override
        public MerchantOffer getOffer(Entity trader, RandomSource random) {
            return new MerchantOffer(new ItemStack(cost.get(), costCount), new ItemStack(result.get(), resultCount),
                    maxUses, xp, 0.05F);
        }
    }
}

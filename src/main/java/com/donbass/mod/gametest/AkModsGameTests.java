package com.donbass.mod.gametest;

import com.donbass.mod.DonbassMod;
import com.donbass.mod.block.WeaponWorkbenchBlockEntity;
import com.donbass.mod.config.DonbassConfig;
import com.donbass.mod.item.AkMods;
import com.donbass.mod.item.AkRifleItem;
import com.donbass.mod.menu.WorkbenchMenu;
import com.donbass.mod.registry.ModBlocks;
import com.donbass.mod.registry.ModItems;
import net.minecraft.core.BlockPos;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.StringTag;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.ContainerLevelAccess;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.gametest.GameTestHolder;
import net.minecraftforge.gametest.PrefixGameTestTemplate;

/**
 * Tests of the 0.3.0 AK modifications and the Weapon Workbench (run with "gradlew runGameTestServer" or
 * "/test runall" in a dev client).  They only need the game's registries and a block entity, not a player
 * in a GUI: the menu is driven through the same calls the server makes for the Install button.
 */
@GameTestHolder(DonbassMod.MOD_ID)
@PrefixGameTestTemplate(false)
public final class AkModsGameTests {
    private static final String ARENA = "gametest/arena";

    private AkModsGameTests() {}

    private static ItemStack kit(AkMods.Mod mod) {
        Item item = switch (mod) {
            case MAGAZINE -> ModItems.AK_MOD_MAGAZINE.get();
            case MECHANISM -> ModItems.AK_MOD_MECHANISM.get();
            case STABILIZER -> ModItems.AK_MOD_STABILIZER.get();
            case BARREL -> ModItems.AK_MOD_BARREL.get();
            case SPRING -> ModItems.AK_MOD_SPRING.get();
        };
        return new ItemStack(item);
    }

    private static boolean near(double a, double b) {
        return Math.abs(a - b) < 1.0E-9D;
    }

    /** The stat formulas, the one-per-kind rule and that installing never touches the loaded rounds. */
    @GameTest(template = ARENA)
    public static void modsChangeTheNumbersAndKeepTheAmmo(GameTestHelper helper) {
        ItemStack rifle = new ItemStack(ModItems.AK_RIFLE.get());
        AkRifleItem.setAmmo(rifle, 17);
        int mag = DonbassConfig.rifleMagazine();
        int reload = DonbassConfig.rifleReloadTicks();
        double spread = DonbassConfig.rifleSpread();
        double interval = DonbassConfig.rifleFireInterval();

        helper.assertTrue(AkMods.get(rifle).isEmpty(), "a fresh rifle must have no mods");
        helper.assertTrue(AkMods.magazineSize(rifle) == mag && AkMods.reloadTicks(rifle) == reload
                && near(AkMods.spread(rifle), spread) && near(AkMods.fireInterval(rifle), interval),
                "without mods the numbers must be the config's");

        helper.assertTrue(AkMods.install(rifle, AkMods.Mod.MAGAZINE), "magazine: install refused");
        helper.assertTrue(AkMods.magazineSize(rifle) == Math.round(mag * 1.5D), "magazine: capacity is not +50 %");
        helper.assertTrue(AkRifleItem.getAmmo(rifle) == 17, "magazine: the loaded rounds were changed by the install");
        helper.assertTrue(!AkMods.install(rifle, AkMods.Mod.MAGAZINE), "magazine: a second install must be refused");

        helper.assertTrue(AkMods.install(rifle, AkMods.Mod.MECHANISM), "mechanism: install refused");
        helper.assertTrue(AkMods.reloadTicks(rifle) == Math.round(reload * 0.8D), "mechanism: reload time is not -20 %");

        helper.assertTrue(AkMods.install(rifle, AkMods.Mod.STABILIZER), "stabilizer: install refused");
        helper.assertTrue(near(AkMods.spread(rifle), spread * 0.8D), "stabilizer: spread is not -20 %");
        helper.assertTrue(AkMods.install(rifle, AkMods.Mod.BARREL), "barrel: install refused");
        helper.assertTrue(near(AkMods.spread(rifle), spread * 0.8D * 0.9D), "barrel: spread is not a further -10 %");

        helper.assertTrue(AkMods.install(rifle, AkMods.Mod.SPRING), "spring: install refused");
        helper.assertTrue(near(AkMods.fireInterval(rifle), interval / 1.1D), "spring: rate of fire is not +10 %");

        helper.assertTrue(AkMods.get(rifle).size() == 5 && rifle.getTag().getList(AkMods.TAG_MODS, 8).size() == 5,
                "five kinds installed once each: the NBT list must have exactly five entries");
        helper.assertTrue(AkRifleItem.getAmmo(rifle) == 17, "the loaded rounds changed while installing mods");

        // a damaged tag: duplicates and unknown ids change nothing
        ItemStack broken = new ItemStack(ModItems.AK_RIFLE.get());
        ListTag list = new ListTag();
        list.add(StringTag.valueOf("spring"));
        list.add(StringTag.valueOf("spring"));
        list.add(StringTag.valueOf("no_such_mod"));
        broken.getOrCreateTag().put(AkMods.TAG_MODS, list);
        helper.assertTrue(AkMods.get(broken).size() == 1 && near(AkMods.fireInterval(broken), interval / 1.1D),
                "duplicate / unknown entries in the NBT must not stack or crash");

        // a reload that was running is cancelled by an install, the rounds stay
        ItemStack reloading = new ItemStack(ModItems.AK_RIFLE.get());
        AkRifleItem.setAmmo(reloading, 3);
        reloading.getOrCreateTag().putLong(AkRifleItem.TAG_RELOAD_END, 12345L);
        AkMods.install(reloading, AkMods.Mod.BARREL);
        helper.assertTrue(!AkRifleItem.isReloading(reloading) && AkRifleItem.getAmmo(reloading) == 3,
                "install: the reload must be cancelled and the ammo kept");
        helper.succeed();
    }

    /** Shot timing: unchanged for a whole interval, right on average (and never bursty) for the spring. */
    @GameTest(template = ARENA)
    public static void shotTimingMatchesTheInterval(GameTestHelper helper) {
        for (int base = 1; base <= 6; base++) {
            for (int used = 0; used < 600; used++) {
                helper.assertTrue(AkMods.isShotTick(base, used) == (used % base == 0),
                        "interval " + base + ", tick " + used + ": a whole interval must behave like used % interval");
            }
        }
        double interval = DonbassConfig.rifleFireInterval() / 1.1D;
        int shots = 0;
        int last = -1;
        for (int used = 0; used < 3000; used++) {
            if (AkMods.isShotTick(interval, used)) {
                if (last >= 0) {
                    int gap = used - last;
                    helper.assertTrue(gap >= Math.floor(interval) && gap <= Math.ceil(interval),
                            "the gap between shots must be floor/ceil of the interval, was " + gap);
                }
                last = used;
                shots++;
            }
        }
        // (with fireIntervalTicks = 1 the rifle already fires every tick: the spring cannot speed that up)
        if (DonbassConfig.rifleFireInterval() >= 2) {
            double expected = 3000.0D / interval;
            helper.assertTrue(Math.abs(shots - expected) <= 1.5D,
                    "expected about " + expected + " shots in 3000 ticks, got " + shots);
        }
        helper.succeed();
    }

    /** The workbench as the server drives it: slots accept only the right things, Install, saving. */
    @GameTest(template = ARENA)
    public static void workbenchInstallsConsumesAndSaves(GameTestHelper helper) {
        BlockPos rel = new BlockPos(3, 1, 3);
        helper.setBlock(rel, ModBlocks.WEAPON_WORKBENCH.get());
        WeaponWorkbenchBlockEntity bench = (WeaponWorkbenchBlockEntity) helper.getBlockEntity(rel);
        helper.assertTrue(bench != null, "the workbench has no block entity");
        WeaponWorkbenchBlockEntity.BenchInventory inv = bench.getInventory();
        Player player = helper.makeMockPlayer();
        WorkbenchMenu menu = new WorkbenchMenu(1, player.getInventory(), inv,
                ContainerLevelAccess.create(helper.getLevel(), helper.absolutePos(rel)));

        helper.assertTrue(inv.isItemValid(WeaponWorkbenchBlockEntity.SLOT_RIFLE, new ItemStack(ModItems.AK_RIFLE.get())),
                "the rifle slot must take the rifle");
        helper.assertTrue(!inv.isItemValid(WeaponWorkbenchBlockEntity.SLOT_RIFLE, kit(AkMods.Mod.BARREL)),
                "the rifle slot must refuse a kit");
        helper.assertTrue(!inv.isItemValid(WeaponWorkbenchBlockEntity.slotOf(AkMods.Mod.STABILIZER),
                kit(AkMods.Mod.MAGAZINE)), "a kit slot must refuse a kit of another kind");
        helper.assertTrue(!inv.isItemValid(WeaponWorkbenchBlockEntity.slotOf(AkMods.Mod.BARREL),
                new ItemStack(ModItems.AK_RIFLE.get())), "a kit slot must refuse the rifle");

        ItemStack rifle = new ItemStack(ModItems.AK_RIFLE.get());
        AkRifleItem.setAmmo(rifle, 11);
        inv.setStackInSlot(WeaponWorkbenchBlockEntity.SLOT_RIFLE, rifle);
        inv.setStackInSlot(WeaponWorkbenchBlockEntity.slotOf(AkMods.Mod.MAGAZINE), kit(AkMods.Mod.MAGAZINE));
        inv.setStackInSlot(WeaponWorkbenchBlockEntity.slotOf(AkMods.Mod.SPRING), kit(AkMods.Mod.SPRING));

        helper.assertTrue(menu.clickMenuButton(player, WorkbenchMenu.BUTTON_INSTALL), "Install did nothing");
        ItemStack result = inv.getStackInSlot(WeaponWorkbenchBlockEntity.SLOT_RIFLE);
        helper.assertTrue(AkMods.has(result, AkMods.Mod.MAGAZINE) && AkMods.has(result, AkMods.Mod.SPRING)
                && AkMods.get(result).size() == 2, "the two kits were not written into the rifle");
        helper.assertTrue(AkRifleItem.getAmmo(result) == 11, "Install changed the loaded rounds");
        helper.assertTrue(inv.getStackInSlot(WeaponWorkbenchBlockEntity.slotOf(AkMods.Mod.MAGAZINE)).isEmpty()
                && inv.getStackInSlot(WeaponWorkbenchBlockEntity.slotOf(AkMods.Mod.SPRING)).isEmpty(),
                "the installed kits must be consumed");

        // a second kit of an installed kind: refused, and NOT consumed
        inv.setStackInSlot(WeaponWorkbenchBlockEntity.slotOf(AkMods.Mod.SPRING), kit(AkMods.Mod.SPRING));
        helper.assertTrue(!menu.clickMenuButton(player, WorkbenchMenu.BUTTON_INSTALL),
                "a duplicate kit must not be installed");
        helper.assertTrue(!inv.getStackInSlot(WeaponWorkbenchBlockEntity.slotOf(AkMods.Mod.SPRING)).isEmpty(),
                "a refused duplicate kit must stay in its slot (no item loss)");
        helper.assertTrue(AkMods.get(inv.getStackInSlot(WeaponWorkbenchBlockEntity.SLOT_RIFLE)).size() == 2,
                "a duplicate install changed the rifle");

        // saving and loading (world save / restart): the contents come back, the mods are still on the rifle
        CompoundTag saved = bench.saveWithoutMetadata();
        WeaponWorkbenchBlockEntity copy = new WeaponWorkbenchBlockEntity(helper.absolutePos(rel), bench.getBlockState());
        copy.load(saved);
        ItemStack loaded = copy.getInventory().getStackInSlot(WeaponWorkbenchBlockEntity.SLOT_RIFLE);
        helper.assertTrue(AkMods.get(loaded).size() == 2 && AkRifleItem.getAmmo(loaded) == 11,
                "after save/load the rifle lost its mods or its rounds");
        helper.assertTrue(!copy.getInventory().getStackInSlot(WeaponWorkbenchBlockEntity.slotOf(AkMods.Mod.SPRING))
                .isEmpty(), "after save/load the kit in the slot is gone");
        helper.succeed();
    }
}

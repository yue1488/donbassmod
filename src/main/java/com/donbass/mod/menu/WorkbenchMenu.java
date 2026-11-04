package com.donbass.mod.menu;

import com.donbass.mod.block.WeaponWorkbenchBlockEntity;
import com.donbass.mod.block.WeaponWorkbenchBlockEntity.BenchInventory;
import com.donbass.mod.item.AkModItem;
import com.donbass.mod.item.AkMods;
import com.donbass.mod.item.AkRifleItem;
import com.donbass.mod.registry.ModBlocks;
import com.donbass.mod.registry.ModMenus;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ContainerData;
import net.minecraft.world.inventory.ContainerLevelAccess;
import net.minecraft.world.inventory.SimpleContainerData;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.items.SlotItemHandler;

/**
 * The menu of the Weapon Workbench: the rifle slot, five kit slots (one per kind), the player's inventory and an
 * "Install" button (menu button 0). All the decisions are made on the server; the stats the screen shows are
 * computed by the server too (from its config) and sent through {@link ContainerData}.
 */
public class WorkbenchMenu extends AbstractContainerMenu {
    public static final int BUTTON_INSTALL = 0;

    public static final int BENCH_SLOTS = WeaponWorkbenchBlockEntity.SLOTS;      // 0 = rifle, 1..5 = kits
    private static final int INV_START = BENCH_SLOTS;
    private static final int INV_END = INV_START + 27;                           // main inventory
    private static final int HOTBAR_END = INV_END + 9;

    // layout of the screen (relative to the GUI's top-left corner)
    public static final int RIFLE_X = 16;
    public static final int ROW_Y = 24;
    public static final int MOD_X0 = 54;
    public static final int MOD_DX = 22;
    public static final int PLAYER_INV_Y = 143;

    // the ContainerData fields
    public static final int DATA_CAPACITY = 0;
    public static final int DATA_RELOAD_TICKS = 1;
    public static final int DATA_RPM = 2;
    public static final int DATA_SPREAD_HUNDREDTHS = 3;
    public static final int DATA_HAS_RIFLE = 4;
    public static final int DATA_COUNT = 5;

    private final BenchInventory bench;
    private final ContainerLevelAccess access;
    private final ContainerData data;

    /** Client side: the real contents and the stats arrive from the server. */
    public WorkbenchMenu(int windowId, Inventory playerInventory) {
        this(windowId, playerInventory, new BenchInventory(() -> { }), ContainerLevelAccess.NULL,
                new SimpleContainerData(DATA_COUNT));
    }

    /** Server side: the inventory is the block entity's. */
    public WorkbenchMenu(int windowId, Inventory playerInventory, BenchInventory bench, ContainerLevelAccess access) {
        this(windowId, playerInventory, bench, access, new StatsData(bench));
    }

    private WorkbenchMenu(int windowId, Inventory playerInventory, BenchInventory bench, ContainerLevelAccess access,
                          ContainerData data) {
        super(ModMenus.WORKBENCH.get(), windowId);
        this.bench = bench;
        this.access = access;
        this.data = data;

        addSlot(new SlotItemHandler(bench, WeaponWorkbenchBlockEntity.SLOT_RIFLE, RIFLE_X, ROW_Y));
        for (AkMods.Mod mod : AkMods.Mod.values()) {
            addSlot(new SlotItemHandler(bench, WeaponWorkbenchBlockEntity.slotOf(mod), modSlotX(mod), ROW_Y));
        }
        for (int row = 0; row < 3; row++) {
            for (int col = 0; col < 9; col++) {
                addSlot(new Slot(playerInventory, 9 + row * 9 + col, 8 + col * 18, PLAYER_INV_Y + row * 18));
            }
        }
        for (int col = 0; col < 9; col++) {
            addSlot(new Slot(playerInventory, col, 8 + col * 18, PLAYER_INV_Y + 58));
        }
        addDataSlots(data);
    }

    public static int modSlotX(AkMods.Mod mod) {
        return MOD_X0 + mod.ordinal() * MOD_DX;
    }

    // ------------------------------------------------------------ queries ----
    public ItemStack getRifle() {
        return slots.get(WeaponWorkbenchBlockEntity.SLOT_RIFLE).getItem();
    }

    public ItemStack getKit(AkMods.Mod mod) {
        return slots.get(WeaponWorkbenchBlockEntity.slotOf(mod)).getItem();
    }

    public boolean hasRifle() {
        return data.get(DATA_HAS_RIFLE) != 0;
    }

    public int stat(int field) {
        return data.get(field);
    }

    /** Is there a kit of this kind in its slot? */
    public boolean hasKit(AkMods.Mod mod) {
        ItemStack kit = getKit(mod);
        return kit.getItem() instanceof AkModItem item && item.mod() == mod;
    }

    /** The kit is in its slot but the rifle already has this kind: it stays in the slot, unused. */
    public boolean isDuplicate(AkMods.Mod mod) {
        ItemStack rifle = getRifle();
        return AkMods.isRifle(rifle) && hasKit(mod) && AkMods.has(rifle, mod);
    }

    /** True if pressing "Install" would do something. */
    public boolean canInstall() {
        ItemStack rifle = getRifle();
        if (!AkMods.isRifle(rifle)) {
            return false;
        }
        for (AkMods.Mod mod : AkMods.Mod.values()) {
            if (hasKit(mod) && !AkMods.has(rifle, mod)) {
                return true;
            }
        }
        return false;
    }

    // ------------------------------------------------------------ install ----
    @Override
    public boolean clickMenuButton(Player player, int id) {
        if (id != BUTTON_INSTALL || player.level().isClientSide) {
            return false;
        }
        ItemStack rifle = bench.getStackInSlot(WeaponWorkbenchBlockEntity.SLOT_RIFLE);
        if (!AkMods.isRifle(rifle)) {
            return false;
        }
        MutableComponent done = null;
        for (AkMods.Mod mod : AkMods.Mod.values()) {
            int slot = WeaponWorkbenchBlockEntity.slotOf(mod);
            ItemStack kit = bench.getStackInSlot(slot);
            if (!(kit.getItem() instanceof AkModItem item) || item.mod() != mod) {
                continue;
            }
            if (!AkMods.install(rifle, mod)) {
                continue;                                    // already has it: the kit is NOT consumed
            }
            bench.setStackInSlot(slot, ItemStack.EMPTY);     // one kit is consumed
            MutableComponent name = Component.translatable(mod.nameKey());
            done = done == null ? name : done.append(Component.literal(", ")).append(name);
        }
        if (done == null) {
            return false;
        }
        // the rifle's NBT was changed in place: tell the handler (it marks the block entity dirty)
        bench.setStackInSlot(WeaponWorkbenchBlockEntity.SLOT_RIFLE, rifle);
        player.displayClientMessage(Component.translatable("message.donbass.workbench_installed", done), true);
        player.level().playSound(null, player.blockPosition(), SoundEvents.ANVIL_USE, SoundSource.BLOCKS, 0.5F, 1.4F);
        return true;
    }

    // --------------------------------------------------------- shift-click ----
    @Override
    public ItemStack quickMoveStack(Player player, int index) {
        Slot slot = slots.get(index);
        if (slot == null || !slot.hasItem()) {
            return ItemStack.EMPTY;
        }
        ItemStack stack = slot.getItem();
        ItemStack original = stack.copy();
        if (index < BENCH_SLOTS) {
            if (!moveItemStackTo(stack, INV_START, HOTBAR_END, true)) {
                return ItemStack.EMPTY;
            }
        } else {
            boolean moved = false;
            if (stack.getItem() instanceof AkRifleItem) {
                moved = moveItemStackTo(stack, WeaponWorkbenchBlockEntity.SLOT_RIFLE,
                        WeaponWorkbenchBlockEntity.SLOT_RIFLE + 1, false);
            } else if (stack.getItem() instanceof AkModItem kit) {
                int target = WeaponWorkbenchBlockEntity.slotOf(kit.mod());
                moved = moveItemStackTo(stack, target, target + 1, false);
            }
            if (!moved) {
                boolean ok = index < INV_END ? moveItemStackTo(stack, INV_END, HOTBAR_END, false)
                        : moveItemStackTo(stack, INV_START, INV_END, false);
                if (!ok) {
                    return ItemStack.EMPTY;
                }
            }
        }
        if (stack.isEmpty()) {
            slot.set(ItemStack.EMPTY);
        } else {
            slot.setChanged();
        }
        if (stack.getCount() == original.getCount()) {
            return ItemStack.EMPTY;
        }
        slot.onTake(player, stack);
        return original;
    }

    @Override
    public boolean stillValid(Player player) {
        return stillValid(access, player, ModBlocks.WEAPON_WORKBENCH.get());
    }

    /** The stats of the rifle in the rifle slot, computed on the server and synchronised as ContainerData. */
    private static final class StatsData implements ContainerData {
        private final BenchInventory bench;

        StatsData(BenchInventory bench) {
            this.bench = bench;
        }

        @Override
        public int get(int index) {
            ItemStack rifle = bench.getStackInSlot(WeaponWorkbenchBlockEntity.SLOT_RIFLE);
            if (!AkMods.isRifle(rifle)) {
                return 0;
            }
            return switch (index) {
                case DATA_CAPACITY -> AkMods.magazineSize(rifle);
                case DATA_RELOAD_TICKS -> AkMods.reloadTicks(rifle);
                case DATA_RPM -> AkMods.roundsPerMinute(rifle);
                case DATA_SPREAD_HUNDREDTHS -> (int) Math.round(AkMods.spread(rifle) * 100.0D);
                case DATA_HAS_RIFLE -> 1;
                default -> 0;
            };
        }

        @Override
        public void set(int index, int value) {
            // read-only
        }

        @Override
        public int getCount() {
            return DATA_COUNT;
        }
    }
}

package com.donbass.mod.block;

import com.donbass.mod.item.AkModItem;
import com.donbass.mod.item.AkMods;
import com.donbass.mod.item.AkRifleItem;
import com.donbass.mod.menu.WorkbenchMenu;
import com.donbass.mod.registry.ModBlockEntities;
import javax.annotation.Nullable;
import net.minecraft.core.BlockPos;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.world.Containers;
import net.minecraft.world.MenuProvider;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ContainerLevelAccess;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraftforge.items.ItemStackHandler;

/**
 * The inventory of a Weapon Workbench: slot 0 holds the rifle, slots 1..5 the kits (slot 1 + Mod.ordinal()).
 * It lives in the block (like a chest), so nothing is lost when the GUI is closed or the player leaves; the
 * contents are dropped when the block is broken.
 */
public class WeaponWorkbenchBlockEntity extends BlockEntity implements MenuProvider {
    public static final int SLOT_RIFLE = 0;
    public static final int SLOTS = 1 + AkMods.Mod.values().length;
    private static final String TAG_INVENTORY = "Inventory";

    private final BenchInventory inventory = new BenchInventory(this::setChanged);

    public WeaponWorkbenchBlockEntity(BlockPos pos, BlockState state) {
        super(ModBlockEntities.WEAPON_WORKBENCH.get(), pos, state);
    }

    public BenchInventory getInventory() {
        return inventory;
    }

    /** Slot index of the kit slot of a mod. */
    public static int slotOf(AkMods.Mod mod) {
        return 1 + mod.ordinal();
    }

    public void dropContents(Level level, BlockPos pos) {
        for (int i = 0; i < inventory.getSlots(); i++) {
            ItemStack stack = inventory.getStackInSlot(i);
            if (!stack.isEmpty()) {
                Containers.dropItemStack(level, pos.getX() + 0.5D, pos.getY() + 0.5D, pos.getZ() + 0.5D, stack);
                inventory.setStackInSlot(i, ItemStack.EMPTY);
            }
        }
    }

    // ------------------------------------------------------------ saving ----
    @Override
    protected void saveAdditional(CompoundTag tag) {
        super.saveAdditional(tag);
        tag.put(TAG_INVENTORY, inventory.serializeNBT());
    }

    @Override
    public void load(CompoundTag tag) {
        super.load(tag);
        inventory.deserializeNBT(tag.getCompound(TAG_INVENTORY));
    }

    // -------------------------------------------------------------- menu ----
    @Override
    public Component getDisplayName() {
        return Component.translatable("block.donbass.weapon_workbench");
    }

    @Nullable
    @Override
    public AbstractContainerMenu createMenu(int windowId, Inventory playerInventory, Player player) {
        return new WorkbenchMenu(windowId, playerInventory, inventory,
                level == null ? ContainerLevelAccess.NULL : ContainerLevelAccess.create(level, worldPosition));
    }

    /**
     * The six slots. The same class is used on the client side (without a block) so that the slots there accept
     * exactly what the server accepts.
     */
    public static final class BenchInventory extends ItemStackHandler {
        private final Runnable onChange;

        public BenchInventory(Runnable onChange) {
            super(SLOTS);
            this.onChange = onChange;
        }

        @Override
        public boolean isItemValid(int slot, ItemStack stack) {
            if (slot == SLOT_RIFLE) {
                return stack.getItem() instanceof AkRifleItem;
            }
            return stack.getItem() instanceof AkModItem kit && slotOf(kit.mod()) == slot;
        }

        @Override
        public int getSlotLimit(int slot) {
            return 1;
        }

        @Override
        protected void onContentsChanged(int slot) {
            if (slot == SLOT_RIFLE) {
                // a rifle taken off the player's hands must not finish a stale reload when it comes back
                AkRifleItem.cancelReload(getStackInSlot(SLOT_RIFLE));
            }
            onChange.run();
        }
    }
}

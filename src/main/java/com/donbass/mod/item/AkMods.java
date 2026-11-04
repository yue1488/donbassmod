package com.donbass.mod.item;

import com.donbass.mod.config.DonbassConfig;
import java.util.EnumSet;
import java.util.Set;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.StringTag;
import net.minecraft.nbt.Tag;
import net.minecraft.world.item.ItemStack;

/**
 * Modifications of the AK (0.3.0). They live in the rifle's own stack NBT, key "AkMods": a list of mod ids
 * (["magazine", "spring"]). Everything that depends on them - magazine size, reload time, fire interval, spread -
 * is computed here from the stack, on top of the values of {@link DonbassConfig}; the rifle code asks this class
 * instead of reading the config directly.
 *
 * <p>Rules: every kind is installed at most once per rifle (a set is read from the NBT, so duplicate or unknown
 * entries in a damaged tag change nothing); modifiers are NOT added up beyond what is listed below; the bullet
 * damage is never touched; "Ammo" and "ReloadEnd" are never touched by installing (the loaded rounds are kept).
 */
public final class AkMods {
    public static final String TAG_MODS = "AkMods";

    /** +50 % magazine size (30 -> 45 with the default config). */
    public static final double MAGAZINE_FACTOR = 1.5D;
    /** -20 % reload time (45 -> 36 ticks). */
    public static final double RELOAD_FACTOR = 0.8D;
    /** -20 % spread. */
    public static final double STABILIZER_SPREAD_FACTOR = 0.8D;
    /** -10 % spread (the barrel does not change the damage). */
    public static final double BARREL_SPREAD_FACTOR = 0.9D;
    /** +10 % rate of fire (the interval between shots is divided by this). */
    public static final double SPRING_RATE_FACTOR = 1.1D;

    private AkMods() {}

    public enum Mod {
        MAGAZINE("magazine"), MECHANISM("mechanism"), STABILIZER("stabilizer"), BARREL("barrel"), SPRING("spring");

        public final String id;

        Mod(String id) {
            this.id = id;
        }

        /** Lang key of the full name ("Extended magazine"), used in the GUI and in messages. */
        public String nameKey() {
            return "gui.donbass.workbench.mod." + id;
        }

        /** Lang key of the short label on the "installed" chip of the workbench. */
        public String chipKey() {
            return "gui.donbass.workbench.chip." + id;
        }

        /** Lang key of the effect description ("+50% magazine capacity ..."). */
        public String effectKey() {
            return "tooltip.donbass.ak_mod_" + id;
        }

        public static Mod byId(String id) {
            for (Mod m : values()) {
                if (m.id.equals(id)) {
                    return m;
                }
            }
            return null;
        }
    }

    // ------------------------------------------------------------ storage ----
    /** The installed mods of a rifle stack; unknown ids are ignored and duplicates collapse. */
    public static Set<Mod> get(ItemStack stack) {
        EnumSet<Mod> result = EnumSet.noneOf(Mod.class);
        CompoundTag tag = stack.getTag();
        if (tag == null || !tag.contains(TAG_MODS, Tag.TAG_LIST)) {
            return result;
        }
        ListTag list = tag.getList(TAG_MODS, Tag.TAG_STRING);
        for (int i = 0; i < list.size(); i++) {
            Mod mod = Mod.byId(list.getString(i));
            if (mod != null) {
                result.add(mod);
            }
        }
        return result;
    }

    public static boolean has(ItemStack stack, Mod mod) {
        return get(stack).contains(mod);
    }

    public static boolean isRifle(ItemStack stack) {
        return stack.getItem() instanceof AkRifleItem;
    }

    /**
     * Writes a mod into the rifle. Returns false (and changes nothing) if the stack is not a rifle or already has
     * this kind. A reload in progress is cancelled (the rifle was off the player's hands at the bench); the
     * loaded rounds ("Ammo") are left alone.
     */
    public static boolean install(ItemStack stack, Mod mod) {
        if (!isRifle(stack)) {
            return false;
        }
        Set<Mod> have = get(stack);
        if (have.contains(mod)) {
            return false;
        }
        have.add(mod);
        write(stack, have);
        AkRifleItem.cancelReload(stack);
        return true;
    }

    private static void write(ItemStack stack, Set<Mod> mods) {
        ListTag list = new ListTag();
        for (Mod m : Mod.values()) {                       // fixed order: the NBT does not depend on install order
            if (mods.contains(m)) {
                list.add(StringTag.valueOf(m.id));
            }
        }
        stack.getOrCreateTag().put(TAG_MODS, list);
    }

    // -------------------------------------------------------------- stats ----
    public static int magazineSize(ItemStack stack) {
        int base = DonbassConfig.rifleMagazine();
        return has(stack, Mod.MAGAZINE) ? (int) Math.max(base, Math.round(base * MAGAZINE_FACTOR)) : base;
    }

    public static int reloadTicks(ItemStack stack) {
        int base = DonbassConfig.rifleReloadTicks();
        return has(stack, Mod.MECHANISM) ? (int) Math.max(1L, Math.round(base * RELOAD_FACTOR)) : base;
    }

    public static double spread(ItemStack stack) {
        double spread = DonbassConfig.rifleSpread();
        Set<Mod> mods = get(stack);
        if (mods.contains(Mod.STABILIZER)) {
            spread *= STABILIZER_SPREAD_FACTOR;
        }
        if (mods.contains(Mod.BARREL)) {
            spread *= BARREL_SPREAD_FACTOR;
        }
        return spread;
    }

    /** Ticks between two shots, fractional with the spring (3 -> 2.727...). */
    public static double fireInterval(ItemStack stack) {
        double base = DonbassConfig.rifleFireInterval();
        return has(stack, Mod.SPRING) ? base / SPRING_RATE_FACTOR : base;
    }

    /** Rounds per minute, for the workbench display. */
    public static int roundsPerMinute(ItemStack stack) {
        return (int) Math.round(1200.0D / fireInterval(stack));
    }

    /**
     * Is a shot due at tick {@code used} of holding the trigger? Shots are at floor(k * interval), k = 0, 1, 2...
     * With a whole interval this is exactly the old "used % interval == 0"; with a fractional one the shots are
     * spread over the ticks so that the average interval is right (2.727 ticks: 0, 2, 5, 8, 10, 13, ...).
     */
    public static boolean isShotTick(double interval, int used) {
        if (used <= 0) {
            return used == 0;
        }
        int k = (int) Math.ceil(used / interval - 1.0E-9D);
        return (int) Math.floor(k * interval + 1.0E-9D) == used;
    }
}

package com.donbass.mod.client;

import com.donbass.mod.item.AkMods;
import com.donbass.mod.menu.WorkbenchMenu;
import com.donbass.mod.registry.ModItems;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import net.minecraft.ChatFormatting;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.inventory.AbstractContainerScreen;
import net.minecraft.network.chat.Component;
import net.minecraft.util.FormattedCharSequence;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;

/**
 * The Weapon Workbench screen, drawn in code in the vanilla style (no GUI texture): the rifle slot, five kit slots
 * with an "installed" chip under each, the Install button, a panel with the rifle's current stats, and the
 * player's inventory. The numbers come from the server (ContainerData); the installed set is read from the
 * rifle stack's NBT, which the slot synchronisation delivers.
 */
public class WorkbenchScreen extends AbstractContainerScreen<WorkbenchMenu> {
    private static final int GUI_W = 176;
    private static final int GUI_H = 225;
    private static final int CHIP_Y = 43;
    private static final int CHIP_W = 18;
    private static final int CHIP_H = 9;
    private static final int PANEL_X0 = 8;
    private static final int PANEL_Y0 = 80;
    private static final int PANEL_X1 = 168;
    private static final int PANEL_Y1 = 128;

    private static final int TEXT_LABEL = 0xFFAAAAAA;
    private static final int TEXT_VALUE = 0xFFFFFFFF;
    private static final int TEXT_BETTER = 0xFF55FF55;

    private Button installButton;

    public WorkbenchScreen(WorkbenchMenu menu, Inventory inventory, Component title) {
        super(menu, inventory, title);
        this.imageWidth = GUI_W;
        this.imageHeight = GUI_H;
        this.titleLabelY = 6;
        this.inventoryLabelY = GUI_H - 94;
    }

    @Override
    protected void init() {
        super.init();
        installButton = addRenderableWidget(Button.builder(Component.translatable("gui.donbass.workbench.install"),
                button -> onInstall()).bounds(leftPos + 16, topPos + 58, 144, 16).build());
    }

    private void onInstall() {
        if (minecraft != null && minecraft.gameMode != null) {
            minecraft.gameMode.handleInventoryButtonClick(menu.containerId, WorkbenchMenu.BUTTON_INSTALL);
        }
    }

    private boolean anyDuplicate() {
        for (AkMods.Mod mod : AkMods.Mod.values()) {
            if (menu.isDuplicate(mod)) {
                return true;
            }
        }
        return false;
    }

    // ------------------------------------------------------------ drawing ----
    @Override
    public void render(GuiGraphics g, int mouseX, int mouseY, float partialTick) {
        boolean can = menu.canInstall();
        installButton.active = can;
        installButton.setMessage(Component.translatable(!can && anyDuplicate()
                ? "gui.donbass.workbench.duplicate" : "gui.donbass.workbench.install"));
        renderBackground(g);
        super.render(g, mouseX, mouseY, partialTick);
        drawDuplicateTint(g);
        renderTooltip(g, mouseX, mouseY);
        drawExtraTooltips(g, mouseX, mouseY);
    }

    @Override
    protected void renderBg(GuiGraphics g, float partialTick, int mouseX, int mouseY) {
        int x = leftPos;
        int y = topPos;
        panel(g, x, y, imageWidth, imageHeight);

        slotFrame(g, x + WorkbenchMenu.RIFLE_X - 1, y + WorkbenchMenu.ROW_Y - 1);
        for (AkMods.Mod mod : AkMods.Mod.values()) {
            slotFrame(g, x + WorkbenchMenu.modSlotX(mod) - 1, y + WorkbenchMenu.ROW_Y - 1);
        }
        for (int row = 0; row < 3; row++) {
            for (int col = 0; col < 9; col++) {
                slotFrame(g, x + 7 + col * 18, y + WorkbenchMenu.PLAYER_INV_Y - 1 + row * 18);
            }
        }
        for (int col = 0; col < 9; col++) {
            slotFrame(g, x + 7 + col * 18, y + WorkbenchMenu.PLAYER_INV_Y + 57);
        }

        // faint icons in the empty bench slots say what goes where
        if (!menu.slots.get(0).hasItem()) {
            ghost(g, new ItemStack(ModItems.AK_RIFLE.get()), x + WorkbenchMenu.RIFLE_X, y + WorkbenchMenu.ROW_Y);
        }
        for (AkMods.Mod mod : AkMods.Mod.values()) {
            if (!menu.hasKit(mod)) {
                ghost(g, new ItemStack(kitItem(mod)), x + WorkbenchMenu.modSlotX(mod), y + WorkbenchMenu.ROW_Y);
            }
        }

        // "installed" chips under the kit slots
        Set<AkMods.Mod> installed = menu.hasRifle() ? AkMods.get(menu.getRifle()) : Set.of();
        for (AkMods.Mod mod : AkMods.Mod.values()) {
            boolean on = installed.contains(mod);
            int cx = x + WorkbenchMenu.modSlotX(mod) - 1;
            int cy = y + CHIP_Y;
            g.fill(cx, cy, cx + CHIP_W, cy + CHIP_H, on ? 0xFF1B5E20 : 0xFF373737);
            g.fill(cx + 1, cy + 1, cx + CHIP_W - 1, cy + CHIP_H - 1, on ? 0xFF2E9E3A : 0xFF4A4A4A);
            g.drawCenteredString(font, Component.translatable(mod.chipKey()), cx + CHIP_W / 2, cy + 1,
                    on ? 0xFFFFFFFF : 0xFF909090);
        }

        drawStatsPanel(g, x, y, installed);
    }

    private void drawStatsPanel(GuiGraphics g, int x, int y, Set<AkMods.Mod> installed) {
        int x0 = x + PANEL_X0;
        int y0 = y + PANEL_Y0;
        int x1 = x + PANEL_X1;
        int y1 = y + PANEL_Y1;
        g.fill(x0 - 1, y0 - 1, x1 + 1, y1 + 1, 0xFF373737);
        g.fill(x0, y0, x1, y1, 0xFF101010);
        if (!menu.hasRifle()) {
            int ty = y0 + 6;
            for (FormattedCharSequence line : font.split(Component.translatable("gui.donbass.workbench.hint"),
                    x1 - x0 - 12)) {
                g.drawString(font, line, x0 + 6, ty, TEXT_LABEL, false);
                ty += 10;
            }
            return;
        }
        int ty = y0 + 6;
        statRow(g, x0, x1, ty, "gui.donbass.workbench.stat.magazine",
                Component.translatable("gui.donbass.workbench.unit.rounds", menu.stat(WorkbenchMenu.DATA_CAPACITY)),
                installed.contains(AkMods.Mod.MAGAZINE));
        statRow(g, x0, x1, ty + 10, "gui.donbass.workbench.stat.reload",
                Component.translatable("gui.donbass.workbench.unit.seconds",
                        String.format(Locale.ROOT, "%.2f", menu.stat(WorkbenchMenu.DATA_RELOAD_TICKS) / 20.0D)),
                installed.contains(AkMods.Mod.MECHANISM));
        statRow(g, x0, x1, ty + 20, "gui.donbass.workbench.stat.rate",
                Component.translatable("gui.donbass.workbench.unit.rpm", menu.stat(WorkbenchMenu.DATA_RPM)),
                installed.contains(AkMods.Mod.SPRING));
        statRow(g, x0, x1, ty + 30, "gui.donbass.workbench.stat.spread",
                Component.translatable("gui.donbass.workbench.unit.degrees",
                        String.format(Locale.ROOT, "%.2f", menu.stat(WorkbenchMenu.DATA_SPREAD_HUNDREDTHS) / 100.0D)),
                installed.contains(AkMods.Mod.STABILIZER) || installed.contains(AkMods.Mod.BARREL));
    }

    /** One line of the stats panel: the label on the left, the value right-aligned (green if a mod improved it). */
    private void statRow(GuiGraphics g, int x0, int x1, int y, String labelKey, Component value, boolean improved) {
        g.drawString(font, Component.translatable(labelKey), x0 + 6, y, TEXT_LABEL, false);
        g.drawString(font, value, x1 - 6 - font.width(value), y, improved ? TEXT_BETTER : TEXT_VALUE, false);
    }

    /** A kit that is in its slot but already installed on this rifle: a red tint over the item. */
    private void drawDuplicateTint(GuiGraphics g) {
        for (AkMods.Mod mod : AkMods.Mod.values()) {
            if (menu.isDuplicate(mod)) {
                int sx = leftPos + WorkbenchMenu.modSlotX(mod);
                int sy = topPos + WorkbenchMenu.ROW_Y;
                g.pose().pushPose();
                g.pose().translate(0.0F, 0.0F, 300.0F);       // above the items (they are drawn at z 150)
                g.fill(sx, sy, sx + 16, sy + 16, 0x80FF2020);
                g.pose().popPose();
            }
        }
    }

    private void drawExtraTooltips(GuiGraphics g, int mouseX, int mouseY) {
        Slot hovered = hoveredSlot;
        if (hovered != null && !hovered.hasItem() && hovered.index < WorkbenchMenu.BENCH_SLOTS) {
            if (hovered.index == 0) {
                g.renderTooltip(font, ModItems.AK_RIFLE.get().getDescription(), mouseX, mouseY);
            } else {
                AkMods.Mod mod = AkMods.Mod.values()[hovered.index - 1];
                g.renderComponentTooltip(font, modLines(mod, null), mouseX, mouseY);
            }
            return;
        }
        Set<AkMods.Mod> installed = menu.hasRifle() ? AkMods.get(menu.getRifle()) : Set.of();
        for (AkMods.Mod mod : AkMods.Mod.values()) {
            int cx = leftPos + WorkbenchMenu.modSlotX(mod) - 1;
            int cy = topPos + CHIP_Y;
            if (mouseX >= cx && mouseX < cx + CHIP_W && mouseY >= cy && mouseY < cy + CHIP_H) {
                g.renderComponentTooltip(font, modLines(mod, installed.contains(mod)), mouseX, mouseY);
                return;
            }
        }
    }

    /** Tooltip lines of a mod: name, effect and (if known) whether the rifle in the slot has it. */
    private static List<Component> modLines(AkMods.Mod mod, Boolean installed) {
        List<Component> lines = new ArrayList<>();
        lines.add(Component.translatable(mod.nameKey()));
        lines.add(Component.translatable(mod.effectKey()).withStyle(ChatFormatting.GREEN));
        if (installed != null) {
            lines.add(Component.translatable(installed ? "gui.donbass.workbench.installed"
                    : "gui.donbass.workbench.not_installed").withStyle(installed ? ChatFormatting.GREEN
                    : ChatFormatting.GRAY));
        }
        return lines;
    }

    private static Item kitItem(AkMods.Mod mod) {
        return switch (mod) {
            case MAGAZINE -> ModItems.AK_MOD_MAGAZINE.get();
            case MECHANISM -> ModItems.AK_MOD_MECHANISM.get();
            case STABILIZER -> ModItems.AK_MOD_STABILIZER.get();
            case BARREL -> ModItems.AK_MOD_BARREL.get();
            case SPRING -> ModItems.AK_MOD_SPRING.get();
        };
    }

    // ------------------------------------------------------ vanilla look ----
    /** The grey vanilla container background with its bevel. */
    private static void panel(GuiGraphics g, int x, int y, int w, int h) {
        g.fill(x, y, x + w, y + h, 0xFF000000);
        g.fill(x + 1, y + 1, x + w - 1, y + h - 1, 0xFFC6C6C6);
        g.fill(x + 1, y + 1, x + w - 2, y + 3, 0xFFFFFFFF);
        g.fill(x + 1, y + 1, x + 3, y + h - 2, 0xFFFFFFFF);
        g.fill(x + 3, y + h - 3, x + w - 1, y + h - 1, 0xFF555555);
        g.fill(x + w - 3, y + 3, x + w - 1, y + h - 1, 0xFF555555);
    }

    /** An 18x18 slot frame whose top-left corner is (x, y); the item is drawn 1 px inside. */
    private static void slotFrame(GuiGraphics g, int x, int y) {
        g.fill(x, y, x + 18, y + 18, 0xFFFFFFFF);
        g.fill(x, y, x + 17, y + 17, 0xFF373737);
        g.fill(x + 1, y + 1, x + 17, y + 17, 0xFF8B8B8B);
    }

    /** An item icon faded into the slot background. */
    private static void ghost(GuiGraphics g, ItemStack icon, int x, int y) {
        g.renderFakeItem(icon, x, y);
        g.pose().pushPose();
        g.pose().translate(0.0F, 0.0F, 200.0F);
        g.fill(x, y, x + 16, y + 16, 0xB08B8B8B);
        g.pose().popPose();
    }
}

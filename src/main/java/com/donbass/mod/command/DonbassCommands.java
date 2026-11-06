package com.donbass.mod.command;

import com.donbass.mod.DonbassMod;
import com.donbass.mod.boss.BossMultiplier;
import com.donbass.mod.boss.BossSettings;
import com.donbass.mod.config.DonbassConfig;
import com.mojang.brigadier.CommandDispatcher;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.builder.LiteralArgumentBuilder;
import com.mojang.brigadier.exceptions.CommandSyntaxException;
import com.mojang.brigadier.exceptions.SimpleCommandExceptionType;
import net.minecraft.ChatFormatting;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.network.chat.Component;
import net.minecraftforge.event.RegisterCommandsEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

/**
 * The commands of the mod (0.4.0), all server side:
 * <ul>
 *   <li>{@code /donbasshelp [section]} - the guide to the mod in short chat blocks; everybody may use it;</li>
 *   <li>{@code /donbass bosshp} - shows the current boss health multiplier; everybody may use it;</li>
 *   <li>{@code /donbass bosshp <multiplier>} - sets it; operators only (permission level 2).</li>
 * </ul>
 * All texts are lang keys ("command.donbass.*"), so every player reads them in his own language.
 */
@Mod.EventBusSubscriber(modid = DonbassMod.MOD_ID, bus = Mod.EventBusSubscriber.Bus.FORGE)
public final class DonbassCommands {
    /** Permission level needed to change the multiplier: the same as for /gamemode, /give ... (an operator). */
    public static final int OP_LEVEL = 2;

    /**
     * Sections of the guide: id, number of text lines ("command.donbass.help.<id>.<n>") and number of command
     * example lines ("command.donbass.help.<id>.ex<n>", printed in another colour). The title of each block is
     * "command.donbass.help.<id>.title". Everything described there exists in the mod; nothing is only planned.
     */
    private record Section(String id, int lines, int examples) {}

    private static final Section[] SECTIONS = {
            new Section("factions", 3, 0),
            new Section("weapons", 3, 0),
            new Section("world", 4, 0),
            new Section("boss", 4, 0),
            new Section("bosshp", 3, 5),
            new Section("coop", 6, 0),
    };

    private DonbassCommands() {}

    @SubscribeEvent
    public static void onRegisterCommands(RegisterCommandsEvent event) {
        CommandDispatcher<CommandSourceStack> dispatcher = event.getDispatcher();

        LiteralArgumentBuilder<CommandSourceStack> help = Commands.literal("donbasshelp")
                .executes(ctx -> help(ctx.getSource(), null));
        for (Section section : SECTIONS) {
            help.then(Commands.literal(section.id()).executes(ctx -> help(ctx.getSource(), section)));
        }
        dispatcher.register(help);

        // The multiplier is a greedy string on purpose: the text is checked by BossMultiplier, so that every bad input
        // ("1,5", "-2", "abc", "1e3", "0") gets the same clear message with the syntax instead of Brigadier's own error.
        dispatcher.register(Commands.literal("donbass")
                .executes(ctx -> usage(ctx.getSource()))
                .then(Commands.literal("help").executes(ctx -> help(ctx.getSource(), null)))
                .then(Commands.literal("bosshp")
                        .executes(ctx -> showBossHealth(ctx.getSource()))
                        .then(Commands.argument("multiplier", StringArgumentType.greedyString())
                                .executes(ctx -> setBossHealth(ctx.getSource(),
                                        StringArgumentType.getString(ctx, "multiplier"))))));
    }

    // ------------------------------------------------------------------- /donbass ----
    private static int usage(CommandSourceStack source) {
        source.sendSuccess(() -> Component.translatable("command.donbass.usage").withStyle(ChatFormatting.YELLOW), false);
        return 1;
    }

    // ------------------------------------------------------------ /donbass bosshp ----
    private static int showBossHealth(CommandSourceStack source) {
        double multiplier = BossSettings.get(source.getServer()).healthMultiplier();
        long health = Math.round(BossMultiplier.health(DonbassConfig.bossHealth(), multiplier));
        source.sendSuccess(() -> Component.translatable("command.donbass.bosshp.current",
                BossMultiplier.format(multiplier), health).withStyle(ChatFormatting.YELLOW), false);
        source.sendSuccess(() -> Component.translatable("command.donbass.bosshp.usage",
                BossMultiplier.format(BossMultiplier.MIN), BossMultiplier.format(BossMultiplier.MAX))
                .withStyle(ChatFormatting.GRAY), false);
        return 1;
    }

    private static int setBossHealth(CommandSourceStack source, String raw) throws CommandSyntaxException {
        if (!source.hasPermission(OP_LEVEL)) {
            throw new SimpleCommandExceptionType(Component.translatable("command.donbass.bosshp.no_permission")).create();
        }
        BossMultiplier.Parsed parsed = BossMultiplier.parse(raw);
        if (!parsed.ok()) {
            String shown = raw.length() > 24 ? raw.substring(0, 24) + "..." : raw;          // keep the chat tidy
            throw new SimpleCommandExceptionType(Component.translatable(parsed.error().key(), shown,
                    BossMultiplier.format(BossMultiplier.MIN), BossMultiplier.format(BossMultiplier.MAX))).create();
        }
        double multiplier = parsed.value();
        BossSettings.get(source.getServer()).setHealthMultiplier(multiplier);                 // saved with the world
        long health = Math.round(BossMultiplier.health(DonbassConfig.bossHealth(), multiplier));
        source.sendSuccess(() -> Component.translatable("command.donbass.bosshp.set",
                BossMultiplier.format(multiplier), health).withStyle(ChatFormatting.GREEN), true);   // true: tell the other operators
        return 1;
    }

    // ----------------------------------------------------------------- /donbasshelp ----
    private static int help(CommandSourceStack source, Section only) {
        if (only == null) {
            source.sendSuccess(() -> Component.translatable("command.donbass.help.title")
                    .withStyle(ChatFormatting.GOLD, ChatFormatting.BOLD), false);
        }
        for (Section section : SECTIONS) {
            if (only == null || only == section) {
                printSection(source, section);
            }
        }
        if (only == null) {
            source.sendSuccess(() -> Component.translatable("command.donbass.help.footer")
                    .withStyle(ChatFormatting.DARK_GRAY), false);
        }
        return 1;
    }

    private static void printSection(CommandSourceStack source, Section section) {
        String base = "command.donbass.help." + section.id();
        source.sendSuccess(() -> Component.translatable(base + ".title")
                .withStyle(ChatFormatting.YELLOW, ChatFormatting.BOLD), false);
        for (int i = 1; i <= section.lines(); i++) {
            String key = base + "." + i;
            source.sendSuccess(() -> Component.translatable(key).withStyle(ChatFormatting.GRAY), false);
        }
        for (int i = 1; i <= section.examples(); i++) {
            String key = base + ".ex" + i;
            source.sendSuccess(() -> Component.translatable(key).withStyle(ChatFormatting.AQUA), false);
        }
    }
}

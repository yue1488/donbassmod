package com.donbass.mod.boss;

import java.math.BigDecimal;
import java.util.Locale;
import java.util.regex.Pattern;

/**
 * The boss health multiplier of {@code /donbass bosshp <multiplier>}: parsing, limits and arithmetic.
 *
 * <p>Pure Java on purpose - no Minecraft classes - so that it can be compiled and run on its own
 * (tools/test_boss_multiplier.sh does exactly that; the game is not needed).
 *
 * <p>Rules: a plain decimal number with a dot ("2", "1.5", "0.75", ".5"); no sign, no exponent, no suffixes (Java's
 * own parser would accept "1e3", "1f", "NaN", "Infinity", "0x10" - none of that is allowed here), not zero, not
 * negative, between {@link #MIN} and {@link #MAX}. The upper limit is the vanilla limit of the max_health attribute
 * (1024) divided by the default boss health (320): 3.2 - above it the multiplier would silently stop doing anything.
 */
public final class BossMultiplier {
    public static final double DEFAULT = 1.0D;
    public static final double MIN = 0.1D;
    public static final double MAX = 3.2D;
    /** The vanilla ceiling of generic.max_health (RangedAttribute); a higher base value is clamped by the game. */
    public static final double ATTRIBUTE_MAX_HEALTH = 1024.0D;

    private static final Pattern NUMBER = Pattern.compile("(\\d+(\\.\\d+)?|\\.\\d+)");

    private BossMultiplier() {}

    /** Why an input was refused; {@link #key()} is the lang key of the message (the usage is part of each text). */
    public enum Error {
        EMPTY("command.donbass.bosshp.error.empty"),
        NOT_A_NUMBER("command.donbass.bosshp.error.format"),
        COMMA("command.donbass.bosshp.error.comma"),
        NEGATIVE("command.donbass.bosshp.error.negative"),
        ZERO("command.donbass.bosshp.error.zero"),
        TOO_SMALL("command.donbass.bosshp.error.min"),
        TOO_LARGE("command.donbass.bosshp.error.max");

        private final String key;

        Error(String key) {
            this.key = key;
        }

        public String key() {
            return key;
        }
    }

    /** Result of {@link #parse}: either a valid value or an error (never both). */
    public record Parsed(double value, Error error) {
        public boolean ok() {
            return error == null;
        }
    }

    public static Parsed parse(String raw) {
        String s = raw == null ? "" : raw.trim();
        if (s.isEmpty()) {
            return fail(Error.EMPTY);
        }
        if (s.indexOf(',') >= 0 && NUMBER.matcher(s.replace(',', '.')).matches()) {
            return fail(Error.COMMA);                            // "1,5": the decimal separator is a dot
        }
        if (s.charAt(0) == '-') {
            return NUMBER.matcher(s.substring(1)).matches() ? fail(Error.NEGATIVE) : fail(Error.NOT_A_NUMBER);
        }
        if (!NUMBER.matcher(s).matches()) {
            return fail(Error.NOT_A_NUMBER);
        }
        double value = Double.parseDouble(s);                    // only digits and one dot here: no NaN, no suffixes
        if (Double.isInfinite(value)) {
            return fail(Error.TOO_LARGE);
        }
        if (value == 0.0D) {
            return fail(Error.ZERO);
        }
        if (value < MIN) {
            return fail(Error.TOO_SMALL);
        }
        if (value > MAX) {
            return fail(Error.TOO_LARGE);
        }
        return new Parsed(Math.round(value * 1000.0D) / 1000.0D, null);   // three decimals are plenty
    }

    private static Parsed fail(Error error) {
        return new Parsed(DEFAULT, error);
    }

    /** A stored value made safe: NaN, infinity, zero, negative or out of range turn into the default / the limit. */
    public static double sanitize(double stored) {
        if (Double.isNaN(stored) || Double.isInfinite(stored) || stored <= 0.0D) {
            return DEFAULT;
        }
        return Math.max(MIN, Math.min(MAX, stored));
    }

    /**
     * The maximum health a new boss gets: the base health (config, 320 by default) times the multiplier, never
     * below 1 and never above the attribute ceiling. This is the ONLY place where the multiplier is applied.
     */
    public static double health(double baseHealth, double multiplier) {
        return Math.max(1.0D, Math.min(ATTRIBUTE_MAX_HEALTH, baseHealth * sanitize(multiplier)));
    }

    /** "1.5", "2", "0.75" - up to three decimals, no trailing zeros, always a dot. */
    public static String format(double multiplier) {
        return new BigDecimal(String.format(Locale.ROOT, "%.3f", multiplier)).stripTrailingZeros().toPlainString();
    }
}

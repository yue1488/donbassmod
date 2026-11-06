import com.donbass.mod.boss.BossMultiplier;
import com.donbass.mod.boss.BossMultiplier.Error;
import com.donbass.mod.boss.BossMultiplier.Parsed;

/**
 * Stand-alone check of the pure logic behind "/donbass bosshp" (no Minecraft needed): run tools/run_selfchecks.sh.
 * It checks the parsing of integers and fractions, every refusal, the limits, the health arithmetic and that the
 * multiplier is never accumulated (the function is pure: the same input always gives the same health).
 */
public class BossMultiplierCheck {
    static int failed = 0;
    static int checks = 0;

    static void ok(boolean cond, String what) {
        checks++;
        if (!cond) {
            failed++;
            System.out.println("FAIL: " + what);
        }
    }

    static void accepts(String in, double expected) {
        Parsed p = BossMultiplier.parse(in);
        ok(p.ok() && Math.abs(p.value() - expected) < 1e-9, "accept \"" + in + "\" -> " + expected + " (got " + p + ")");
    }

    static void refuses(String in, Error expected) {
        Parsed p = BossMultiplier.parse(in);
        ok(!p.ok() && p.error() == expected, "refuse \"" + in + "\" with " + expected + " (got " + p + ")");
    }

    public static void main(String[] args) {
        // integers and fractions from the task
        accepts("1", 1.0); accepts("1.0", 1.0); accepts("2", 2.0); accepts("1.5", 1.5); accepts("3", 3.0);
        accepts("0.75", 0.75); accepts(".5", 0.5); accepts("2.5", 2.5); accepts("  1.5  ", 1.5);
        accepts("0.1", 0.1); accepts("3.2", 3.2); accepts("3.20", 3.2); accepts("1.2345", 1.235);
        accepts("0001.5", 1.5);
        // refused: syntax
        refuses("", Error.EMPTY); refuses("   ", Error.EMPTY); refuses(null, Error.EMPTY);
        refuses("abc", Error.NOT_A_NUMBER); refuses("1e3", Error.NOT_A_NUMBER); refuses("1f", Error.NOT_A_NUMBER);
        refuses("1d", Error.NOT_A_NUMBER); refuses("NaN", Error.NOT_A_NUMBER); refuses("Infinity", Error.NOT_A_NUMBER);
        refuses("0x10", Error.NOT_A_NUMBER); refuses("1.5.2", Error.NOT_A_NUMBER); refuses("1 2", Error.NOT_A_NUMBER);
        refuses("+2", Error.NOT_A_NUMBER); refuses("--1", Error.NOT_A_NUMBER); refuses("1.", Error.NOT_A_NUMBER);
        refuses("x1.5", Error.NOT_A_NUMBER); refuses("2x", Error.NOT_A_NUMBER); refuses("-", Error.NOT_A_NUMBER);
        refuses("1,5", Error.COMMA); refuses("0,75", Error.COMMA); refuses("1,5,5", Error.NOT_A_NUMBER);
        // refused: sign and range
        refuses("-1", Error.NEGATIVE); refuses("-0.5", Error.NEGATIVE); refuses("-0", Error.NEGATIVE);
        refuses("0", Error.ZERO); refuses("0.0", Error.ZERO); refuses("0.000", Error.ZERO);
        refuses("0.05", Error.TOO_SMALL); refuses("0.099", Error.TOO_SMALL);
        refuses("3.21", Error.TOO_LARGE); refuses("4", Error.TOO_LARGE); refuses("100", Error.TOO_LARGE);
        refuses("99999999999999999999999999", Error.TOO_LARGE);
        StringBuilder huge = new StringBuilder();
        for (int i = 0; i < 400; i++) huge.append('9');
        refuses(huge.toString(), Error.TOO_LARGE);                      // overflows to Infinity in Double.parseDouble
        // the co-op table of /donbasshelp is inside the limits
        for (String m : new String[] {"1.0", "1.5", "2.0", "2.5", "3.0"}) accepts(m, Double.parseDouble(m));

        // health arithmetic with the default 320 HP
        ok(BossMultiplier.health(320, 1.0) == 320.0, "x1 = 320");
        ok(BossMultiplier.health(320, 2.0) == 640.0, "x2 = 640");
        ok(BossMultiplier.health(320, 1.5) == 480.0, "x1.5 = 480");
        ok(BossMultiplier.health(320, 3.0) == 960.0, "x3 = 960");
        ok(BossMultiplier.health(320, 0.75) == 240.0, "x0.75 = 240");
        ok(BossMultiplier.health(320, 3.2) == 1024.0, "x3.2 = 1024 (the attribute limit)");
        ok(BossMultiplier.health(5000, 1.0) == 1024.0, "a config health above the ceiling is clamped");
        ok(BossMultiplier.health(40, 0.1) == 4.0, "the smallest config health with the smallest multiplier");
        ok(BossMultiplier.health(320, Double.NaN) == 320.0, "a NaN multiplier falls back to 1.0");
        ok(BossMultiplier.health(320, -3) == 320.0, "a negative stored multiplier falls back to 1.0");
        ok(BossMultiplier.health(320, 0) == 320.0, "a zero stored multiplier falls back to 1.0");
        ok(BossMultiplier.health(320, 99) == 1024.0, "an out-of-range stored multiplier is clamped to 3.2");
        // not accumulating: applying the same setting any number of times to the base value gives the same health
        double h = 0;
        for (int i = 0; i < 5; i++) h = BossMultiplier.health(320, 2.0);
        ok(h == 640.0, "repeated use is not cumulative");
        // sanitize
        ok(BossMultiplier.sanitize(Double.POSITIVE_INFINITY) == 1.0, "sanitize(inf) = 1");
        ok(BossMultiplier.sanitize(0.01) == BossMultiplier.MIN, "sanitize(0.01) = MIN");
        ok(BossMultiplier.sanitize(1.7) == 1.7, "sanitize keeps valid values");
        // format
        ok(BossMultiplier.format(1.0).equals("1"), "format 1.0 -> 1 (got " + BossMultiplier.format(1.0) + ")");
        ok(BossMultiplier.format(1.5).equals("1.5"), "format 1.5");
        ok(BossMultiplier.format(0.75).equals("0.75"), "format 0.75");
        ok(BossMultiplier.format(3.2).equals("3.2"), "format 3.2");
        ok(BossMultiplier.format(10.0).equals("10"), "format 10 (plain, not 1E+1)");
        ok(BossMultiplier.format(1.235).equals("1.235"), "format 1.235");
        // every refusal has its own lang key
        java.util.Set<String> keys = new java.util.HashSet<>();
        for (Error e : Error.values()) keys.add(e.key());
        ok(keys.size() == Error.values().length, "the refusals have distinct lang keys");

        System.out.println(checks + " checks, " + failed + " failed");
        if (failed > 0) System.exit(1);
    }
}

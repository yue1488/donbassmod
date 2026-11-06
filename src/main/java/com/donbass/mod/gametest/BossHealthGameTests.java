package com.donbass.mod.gametest;

import com.donbass.mod.DonbassMod;
import com.donbass.mod.boss.BossMultiplier;
import com.donbass.mod.boss.BossSettings;
import com.donbass.mod.config.DonbassConfig;
import com.donbass.mod.entity.CombineDirectorEntity;
import com.donbass.mod.registry.ModEntities;
import java.util.UUID;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.nbt.CompoundTag;
import net.minecraftforge.gametest.GameTestHolder;
import net.minecraftforge.gametest.PrefixGameTestTemplate;

/**
 * Tests of the boss health multiplier of "/donbass bosshp" (0.4.0): it is applied once, to a new boss only, it
 * survives a save / load of the boss, and the phases follow it. Run them like BossGameTests
 * ("gradlew runGameTestServer"). The parsing and the limits are tested without the game by tools/run_selfchecks.sh.
 * Every test sets the multiplier it needs first and puts it back to 1.0 at the end.
 */
@GameTestHolder(DonbassMod.MOD_ID)
@PrefixGameTestTemplate(false)
public final class BossHealthGameTests {
    private static final String ARENA = "gametest/arena";

    private BossHealthGameTests() {}

    private static BossSettings settings(GameTestHelper helper) {
        return BossSettings.get(helper.getLevel().getServer());
    }

    private static double expectedHealth(double multiplier) {
        return BossMultiplier.health(DonbassConfig.bossHealth(), multiplier);
    }

    /** x2 gives twice the health; a later change does not touch the standing boss; save / load does not apply it again. */
    @GameTest(template = ARENA, timeoutTicks = 200)
    public static void multiplierIsAppliedOnceToANewBossOnly(GameTestHelper helper) {
        settings(helper).setHealthMultiplier(2.0D);
        CombineDirectorEntity boss = helper.spawn(ModEntities.COMBINE_DIRECTOR.get(), 7, 1, 7);
        helper.runAfterDelay(5, () -> {
            helper.assertTrue(Math.abs(boss.getMaxHealth() - expectedHealth(2.0D)) < 0.01D,
                    "x2: max health should be " + expectedHealth(2.0D) + ", was " + boss.getMaxHealth());
            helper.assertTrue(Math.abs(boss.getHealth() - boss.getMaxHealth()) < 0.01D, "a new boss must start at full health");
            settings(helper).setHealthMultiplier(3.0D);                    // the command is used while the boss stands
        });
        helper.runAfterDelay(40, () -> {
            helper.assertTrue(Math.abs(boss.getMaxHealth() - expectedHealth(2.0D)) < 0.01D,
                    "a boss that already stands must keep its health, was " + boss.getMaxHealth());
            CompoundTag saved = new CompoundTag();
            boss.saveWithoutId(saved);
            saved.putUUID("UUID", UUID.randomUUID());
            CombineDirectorEntity copy = ModEntities.COMBINE_DIRECTOR.get().create(helper.getLevel());
            helper.assertTrue(copy != null, "could not create a second boss");
            copy.load(saved);
            boss.discard();
            helper.getLevel().addFreshEntity(copy);
            helper.runAfterDelay(40, () -> {
                helper.assertTrue(Math.abs(copy.getMaxHealth() - expectedHealth(2.0D)) < 0.01D,
                        "a reloaded boss must not get the multiplier again (x3 is set now), was " + copy.getMaxHealth());
                settings(helper).setHealthMultiplier(BossMultiplier.DEFAULT);
                helper.succeed();
            });
        });
    }

    /** x3: the phase changes still happen at 66 % and 33 % of the (bigger) health, and the boss takes damage in each. */
    @GameTest(template = ARENA, timeoutTicks = 400)
    public static void phasesFollowTheMultiplier(GameTestHelper helper) {
        settings(helper).setHealthMultiplier(3.0D);
        CombineDirectorEntity boss = helper.spawn(ModEntities.COMBINE_DIRECTOR.get(), 7, 1, 7);
        helper.runAfterDelay(5, () -> {
            helper.assertTrue(boss.getPhase() == 1, "a fresh boss must be in phase 1");
            boss.setHealth(boss.getMaxHealth() * 0.60F);
        });
        helper.runAfterDelay(8, () -> helper.assertTrue(boss.getPhase() == 2,
                "x3: expected phase 2 at 60 % of the health, was " + boss.getPhase()));
        helper.runAfterDelay(100, () -> {
            boss.invulnerableTime = 0;
            float before = boss.getHealth();
            helper.assertTrue(boss.hurt(helper.getLevel().damageSources().generic(), 10.0F), "x3, phase 2: the hit was refused");
            helper.assertTrue(boss.getHealth() < before, "x3, phase 2: health did not drop");
            boss.invulnerableTime = 0;
            boss.setHealth(boss.getMaxHealth() * 0.30F);
        });
        helper.runAfterDelay(104, () -> helper.assertTrue(boss.getPhase() == 3,
                "x3: expected phase 3 at 30 % of the health, was " + boss.getPhase()));
        helper.runAfterDelay(200, () -> {
            boss.invulnerableTime = 0;
            float before = boss.getHealth();
            helper.assertTrue(boss.hurt(helper.getLevel().damageSources().generic(), 10.0F), "x3, phase 3: the hit was refused");
            helper.assertTrue(boss.getHealth() < before, "x3, phase 3: health did not drop");
            settings(helper).setHealthMultiplier(BossMultiplier.DEFAULT);
            helper.succeed();
        });
    }
}

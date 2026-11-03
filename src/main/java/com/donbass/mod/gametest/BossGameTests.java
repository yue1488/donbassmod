package com.donbass.mod.gametest;

import com.donbass.mod.DonbassMod;
import com.donbass.mod.entity.CombineDirectorEntity;
import com.donbass.mod.registry.ModEntities;
import java.util.UUID;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraftforge.gametest.GameTestHolder;
import net.minecraftforge.gametest.PrefixGameTestTemplate;

/**
 * Regression tests for the boss (run them with "gradlew runGameTestServer" or "/test runall" in a dev client).
 * They exist because of the 0.2.0 bug "the boss takes no damage from phase 2 on": the phase-change lock was
 * implemented through isImmobile(), which stops the AI step, so the lock's timer never ran out.
 * Everything here is driven by game time, so the tests do not need a player.
 */
@GameTestHolder(DonbassMod.MOD_ID)
@PrefixGameTestTemplate(false)
public final class BossGameTests {
    private static final String ARENA = "gametest/arena";

    private BossGameTests() {}

    private static CombineDirectorEntity spawnBoss(GameTestHelper helper) {
        return helper.spawn(ModEntities.COMBINE_DIRECTOR.get(), 7, 1, 7);
    }

    /** A plain hit: it must go through the invulnerability frames, armour and the phase rules. */
    private static DamageSource hit(GameTestHelper helper) {
        return helper.getLevel().damageSources().generic();
    }

    /** The whole fight in game time: phase 1 -> 2 -> 3 -> death, damage must work wherever it is allowed. */
    @GameTest(template = ARENA, timeoutTicks = 400)
    public static void bossTakesDamageInEveryPhase(GameTestHelper helper) {
        CombineDirectorEntity boss = spawnBoss(helper);

        helper.runAfterDelay(5, () -> {                       // the first AI step has set the boss up by now
            helper.assertTrue(boss.getPhase() == 1, "a fresh boss must be in phase 1, was " + boss.getPhase());
            float before = boss.getHealth();
            helper.assertTrue(boss.hurt(hit(helper), 5.0F), "phase 1: the hit was refused");
            helper.assertTrue(boss.getHealth() < before, "phase 1: health did not drop");
            boss.invulnerableTime = 0;
            boss.setHealth(boss.getMaxHealth() * 0.60F);      // below 66 %: phase 2 starts
        });
        helper.runAfterDelay(8, () -> {
            helper.assertTrue(boss.getPhase() == 2, "expected phase 2, was " + boss.getPhase());
            helper.assertTrue(boss.isLocked(), "the boss should be in its phase change roar");
            float before = boss.getHealth();
            helper.assertTrue(!boss.hurt(hit(helper), 5.0F) && boss.getHealth() == before,
                    "the roar is the only moment when the boss may be invulnerable");
        });
        helper.runAfterDelay(100, () -> {                     // the roar lasts 60 ticks
            helper.assertTrue(!boss.isLocked(), "phase 2: still locked 100 ticks after the phase change");
            boss.invulnerableTime = 0;
            float before = boss.getHealth();
            helper.assertTrue(boss.hurt(hit(helper), 10.0F), "phase 2: the hit was refused (the 0.2.0 bug)");
            helper.assertTrue(boss.getHealth() < before, "phase 2: health did not drop");
            boss.invulnerableTime = 0;
            boss.setHealth(boss.getMaxHealth() * 0.30F);      // below 33 %: phase 3 starts
        });
        helper.runAfterDelay(104, () ->
                helper.assertTrue(boss.getPhase() == 3, "expected phase 3, was " + boss.getPhase()));
        helper.runAfterDelay(200, () -> {
            helper.assertTrue(!boss.isLocked(), "phase 3: still locked 200 ticks after the phase change");
            boss.invulnerableTime = 0;
            float before = boss.getHealth();
            helper.assertTrue(boss.hurt(hit(helper), 10.0F), "phase 3: the hit was refused");
            helper.assertTrue(boss.getHealth() < before, "phase 3: health did not drop");
            boss.invulnerableTime = 0;
            boss.setHealth(1.0F);
            boss.hurt(hit(helper), 10.0F);
            helper.assertTrue(boss.isDeadOrDying(), "the boss did not die from a lethal hit");
            helper.succeed();
        });
    }

    /** A boss saved to disk in phase 2 must come back in phase 2 and still take damage. */
    @GameTest(template = ARENA, timeoutTicks = 300)
    public static void bossReloadedInPhaseTwoTakesDamage(GameTestHelper helper) {
        CombineDirectorEntity boss = spawnBoss(helper);
        helper.runAfterDelay(5, () -> boss.setHealth(boss.getMaxHealth() * 0.5F));
        helper.runAfterDelay(100, () -> {
            helper.assertTrue(boss.getPhase() == 2, "expected phase 2, was " + boss.getPhase());
            CompoundTag saved = new CompoundTag();
            boss.saveWithoutId(saved);
            saved.putUUID("UUID", UUID.randomUUID());          // the copy must not share the original's identity
            CombineDirectorEntity copy = ModEntities.COMBINE_DIRECTOR.get().create(helper.getLevel());
            helper.assertTrue(copy != null, "could not create a second boss");
            copy.load(saved);
            boss.discard();
            helper.getLevel().addFreshEntity(copy);
            helper.assertTrue(copy.getPhase() == 2, "the saved phase was lost");
            helper.runAfterDelay(5, () -> {
                helper.assertTrue(!copy.isLocked(), "a reloaded boss must not be locked");
                copy.invulnerableTime = 0;
                float before = copy.getHealth();
                helper.assertTrue(copy.hurt(hit(helper), 10.0F), "reloaded boss: the hit was refused");
                helper.assertTrue(copy.getHealth() < before, "reloaded boss: health did not drop");
                helper.succeed();
            });
        });
    }
}

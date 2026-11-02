package com.donbass.mod.client;

/** Plain client-side animation state of the rifle (no Minecraft types, safe to load on a server). */
public final class RifleClientState {
    /** 1.0 right after a shot, decays towards 0. */
    public static volatile float recoil;

    private RifleClientState() {}

    public static void kick() {
        recoil = 1.0F;
    }

    public static void tick() {
        recoil *= 0.55F;
        if (recoil < 0.01F) {
            recoil = 0.0F;
        }
    }
}

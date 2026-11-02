package com.donbass.mod.client;

import net.minecraft.client.Minecraft;
import net.minecraft.world.entity.player.Player;

/** Client-only reactions of the rifle. Only ever called through DistExecutor on the physical client. */
public final class ClientHooks {
    private ClientHooks() {}

    public static void onRifleShot(Player shooter) {
        if (shooter != Minecraft.getInstance().player) {
            return;                                   // somebody else's shot: no kick on my screen
        }
        RifleClientState.kick();
        // a small camera kick up and to a random side
        shooter.setXRot(shooter.getXRot() - 0.45F);
        shooter.setYRot(shooter.getYRot() + (shooter.getRandom().nextFloat() - 0.5F) * 0.5F);
    }
}

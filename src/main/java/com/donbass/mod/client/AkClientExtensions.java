package com.donbass.mod.client;

import com.donbass.mod.config.DonbassConfig;
import com.donbass.mod.item.AkRifleItem;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import net.minecraft.client.Minecraft;
import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.util.Mth;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.HumanoidArm;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.client.extensions.common.IClientItemExtensions;

/**
 * How the AK looks in hand: a two-handed rifle pose in third person (crossbow hold, crossbow charge while
 * reloading) and a custom first-person transform with recoil and a reload dip.
 */
public class AkClientExtensions implements IClientItemExtensions {
    @Override
    public HumanoidModel.ArmPose getArmPose(LivingEntity entity, InteractionHand hand, ItemStack stack) {
        return AkRifleItem.isReloading(stack) ? HumanoidModel.ArmPose.CROSSBOW_CHARGE
                : HumanoidModel.ArmPose.CROSSBOW_HOLD;
    }

    /**
     * Replaces the vanilla first-person hand transform for this item (equip lift included).
     * Intentionally without @Override: if the signature differs in a Forge build the method is simply unused.
     */
    public boolean applyForgeHandTransform(PoseStack poseStack, LocalPlayer player, HumanoidArm arm, ItemStack stack,
                                           float partialTick, float equipProcess, float swingProcess) {
        int side = arm == HumanoidArm.RIGHT ? 1 : -1;
        poseStack.translate(side * 0.56F, -0.52F + equipProcess * -0.6F, -0.72F);

        float recoil = RifleClientState.recoil;
        poseStack.translate(0.0F, recoil * 0.015F, recoil * 0.09F);
        poseStack.mulPose(Axis.XP.rotationDegrees(-recoil * 3.5F));

        if (AkRifleItem.isReloading(stack) && Minecraft.getInstance().level != null) {
            float total = Math.max(1, DonbassConfig.rifleReloadTicks());
            float left = AkRifleItem.getReloadEnd(stack) - (Minecraft.getInstance().level.getGameTime() + partialTick);
            float progress = Mth.clamp(1.0F - left / total, 0.0F, 1.0F);
            float dip = Mth.sin(progress * (float) Math.PI);             // down and back up
            poseStack.translate(0.0F, -0.22F * dip, 0.05F * dip);
            poseStack.mulPose(Axis.XP.rotationDegrees(38.0F * dip));
            poseStack.mulPose(Axis.ZP.rotationDegrees(side * -14.0F * dip));
        }
        return true;
    }
}

package com.donbass.mod.client;

import com.donbass.mod.entity.MilitiaEntity;
import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/** Humanoid body that holds the rifle with both hands; the state is synced from the entity. */
public class MilitiaModel extends HumanoidModel<MilitiaEntity> {
    public MilitiaModel(ModelPart root) {
        super(root);
    }

    @Override
    public void prepareMobModel(MilitiaEntity entity, float limbSwing, float limbSwingAmount, float partialTick) {
        HumanoidModel.ArmPose pose = entity.getCombatState() == MilitiaEntity.STATE_RELOADING
                ? HumanoidModel.ArmPose.CROSSBOW_CHARGE
                : HumanoidModel.ArmPose.CROSSBOW_HOLD;
        if (entity.isHoldingRifle()) {
            this.rightArmPose = pose;
            this.leftArmPose = pose;
        } else {
            this.rightArmPose = HumanoidModel.ArmPose.EMPTY;
            this.leftArmPose = HumanoidModel.ArmPose.EMPTY;
        }
        super.prepareMobModel(entity, limbSwing, limbSwingAmount, partialTick);
    }

    @Override
    public void setupAnim(MilitiaEntity entity, float limbSwing, float limbSwingAmount, float ageInTicks,
                          float netHeadYaw, float headPitch) {
        super.setupAnim(entity, limbSwing, limbSwingAmount, ageInTicks, netHeadYaw, headPitch);
        int state = entity.getCombatState();
        if (state == MilitiaEntity.STATE_RELOADING) {
            // the off hand works the magazine: pulls down and back in a rhythm
            float t = ageInTicks * 0.55F;
            this.leftArm.xRot = -0.95F + Mth.sin(t) * 0.4F;
            this.leftArm.yRot = 0.45F;
            this.rightArm.xRot = -1.15F;
            this.head.xRot += 0.18F;                                  // looks down at the weapon
        } else if (state == MilitiaEntity.STATE_FIRING) {
            this.rightArm.xRot += 0.16F;                              // recoil
            this.leftArm.xRot += 0.10F;
            this.head.xRot -= 0.05F;
        }
    }
}

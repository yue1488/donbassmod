package com.donbass.mod.client;

import com.donbass.mod.entity.CombineDirectorEntity;
import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/** Humanoid body of the boss: holds the rifle two-handed; both arms go up for the ground slam and out for the roar. */
public class DirectorModel extends HumanoidModel<CombineDirectorEntity> {
    public DirectorModel(ModelPart root) {
        super(root);
    }

    @Override
    public void prepareMobModel(CombineDirectorEntity entity, float limbSwing, float limbSwingAmount, float partialTick) {
        HumanoidModel.ArmPose pose = entity.getBossPose() == CombineDirectorEntity.POSE_NORMAL && entity.isHoldingRifle()
                ? HumanoidModel.ArmPose.CROSSBOW_HOLD : HumanoidModel.ArmPose.EMPTY;
        this.rightArmPose = pose;
        this.leftArmPose = pose;
        super.prepareMobModel(entity, limbSwing, limbSwingAmount, partialTick);
    }

    @Override
    public void setupAnim(CombineDirectorEntity entity, float limbSwing, float limbSwingAmount, float ageInTicks,
                          float netHeadYaw, float headPitch) {
        super.setupAnim(entity, limbSwing, limbSwingAmount, ageInTicks, netHeadYaw, headPitch);
        int pose = entity.getBossPose();
        if (pose == CombineDirectorEntity.POSE_SLAM) {                       // the hammer is up
            float tremble = Mth.sin(ageInTicks * 0.9F) * 0.06F;
            this.rightArm.xRot = -2.9F + tremble;
            this.leftArm.xRot = -2.9F - tremble;
            this.rightArm.zRot = 0.14F;
            this.leftArm.zRot = -0.14F;
            this.head.xRot -= 0.25F;
        } else if (pose == CombineDirectorEntity.POSE_ROAR) {                // arms wide, head thrown back
            this.rightArm.xRot = -0.5F;
            this.leftArm.xRot = -0.5F;
            this.rightArm.zRot = 1.25F + Mth.sin(ageInTicks * 0.7F) * 0.08F;
            this.leftArm.zRot = -1.25F - Mth.sin(ageInTicks * 0.7F) * 0.08F;
            this.head.xRot -= 0.6F;
        }
    }
}

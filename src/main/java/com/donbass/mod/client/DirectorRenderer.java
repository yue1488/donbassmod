package com.donbass.mod.client;

import com.donbass.mod.DonbassMod;
import com.donbass.mod.entity.CombineDirectorEntity;
import com.mojang.blaze3d.vertex.PoseStack;
import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.model.geom.ModelLayers;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.HumanoidMobRenderer;
import net.minecraft.client.renderer.entity.layers.HumanoidArmorLayer;
import net.minecraft.resources.ResourceLocation;

/** The boss: a humanoid 1.25 times larger than usual, with its own skin and the coal armour on top. */
public class DirectorRenderer extends HumanoidMobRenderer<CombineDirectorEntity, DirectorModel> {
    private static final ResourceLocation TEXTURE =
            new ResourceLocation(DonbassMod.MOD_ID, "textures/entity/combine_director.png");
    private static final float SCALE = 1.25F;

    public DirectorRenderer(EntityRendererProvider.Context context) {
        super(context, new DirectorModel(context.bakeLayer(ModelLayers.ZOMBIE)), 0.9F);
        this.addLayer(new HumanoidArmorLayer<>(this,
                new HumanoidModel<>(context.bakeLayer(ModelLayers.ZOMBIE_INNER_ARMOR)),
                new HumanoidModel<>(context.bakeLayer(ModelLayers.ZOMBIE_OUTER_ARMOR)),
                context.getModelManager()));
    }

    @Override
    public ResourceLocation getTextureLocation(CombineDirectorEntity entity) {
        return TEXTURE;
    }

    @Override
    protected void scale(CombineDirectorEntity entity, PoseStack poseStack, float partialTick) {
        poseStack.scale(SCALE, SCALE, SCALE);
    }
}

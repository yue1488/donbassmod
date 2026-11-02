package com.donbass.mod.client;

import com.donbass.mod.DonbassMod;
import com.donbass.mod.entity.MinerEntity;
import com.mojang.blaze3d.vertex.PoseStack;
import net.minecraft.client.model.VillagerModel;
import net.minecraft.client.model.geom.ModelLayers;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.MobRenderer;
import net.minecraft.client.renderer.entity.layers.CrossedArmsItemLayer;
import net.minecraft.client.renderer.entity.layers.CustomHeadLayer;
import net.minecraft.resources.ResourceLocation;

/** Villager-shaped body with the miner skin, crossed arms holding the pickaxe. */
public class MinerRenderer extends MobRenderer<MinerEntity, VillagerModel<MinerEntity>> {
    private static final ResourceLocation TEXTURE =
            new ResourceLocation(DonbassMod.MOD_ID, "textures/entity/miner.png");

    public MinerRenderer(EntityRendererProvider.Context context) {
        super(context, new VillagerModel<>(context.bakeLayer(ModelLayers.VILLAGER)), 0.5F);
        this.addLayer(new CustomHeadLayer<>(this, context.getModelSet(), context.getItemInHandRenderer()));
        this.addLayer(new CrossedArmsItemLayer<>(this, context.getItemInHandRenderer()));
    }

    @Override
    public ResourceLocation getTextureLocation(MinerEntity entity) {
        return TEXTURE;
    }

    @Override
    protected void scale(MinerEntity entity, PoseStack poseStack, float partialTick) {
        float scale = 0.9375F;
        poseStack.scale(scale, scale, scale);
    }
}

package com.donbass.mod.client;

import com.donbass.mod.DonbassMod;
import com.donbass.mod.entity.MilitiaEntity;
import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.model.geom.ModelLayers;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.HumanoidMobRenderer;
import net.minecraft.client.renderer.entity.layers.HumanoidArmorLayer;
import net.minecraft.resources.ResourceLocation;

/** Renders a fighter of either squad: own skin, worn armour, rifle in hand (layers of HumanoidMobRenderer). */
public class MilitiaRenderer extends HumanoidMobRenderer<MilitiaEntity, MilitiaModel> {
    private final ResourceLocation texture;

    public MilitiaRenderer(EntityRendererProvider.Context context, String skin) {
        super(context, new MilitiaModel(context.bakeLayer(ModelLayers.ZOMBIE)), 0.5F);
        this.texture = new ResourceLocation(DonbassMod.MOD_ID, "textures/entity/" + skin + ".png");
        this.addLayer(new HumanoidArmorLayer<>(this,
                new HumanoidModel<>(context.bakeLayer(ModelLayers.ZOMBIE_INNER_ARMOR)),
                new HumanoidModel<>(context.bakeLayer(ModelLayers.ZOMBIE_OUTER_ARMOR)),
                context.getModelManager()));
    }

    @Override
    public ResourceLocation getTextureLocation(MilitiaEntity entity) {
        return texture;
    }
}

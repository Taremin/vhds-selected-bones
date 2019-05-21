import bpy

bl_info = {
    "name": "Voxel Heat Diffuse Skinning - Only selected bones",
    "author": "Taremin",
    "version": (0, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Tools > Animation",
    "description": "Voxel Heat Diffuse Skinning - Only selected bones",
    "warning": "",
    "category": "Object"
}

IS_LEGACY = (bpy.app.version < (2, 80, 0))


def select(obj, value):
    if IS_LEGACY:
        obj.select = value
    else:
        obj.select_set(value)


def get_active_object():
    if IS_LEGACY:
        return bpy.context.scene.objects.active
    else:
        return bpy.context.window.view_layer.objects.active


def set_active_object(obj):
    if IS_LEGACY:
        bpy.context.scene.objects.active = obj
    else:
        bpy.context.window.view_layer.objects.active = obj


class VHDSOnlySelectedBonesPrepareOperator(bpy.types.Operator):
    bl_idname = "wm.voxel_heat_diffuse_only_selected_bones_prepare"
    bl_label = "Preapre"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # mirror object
        bpy.context.scene.vhdsosb_selected_objects.clear()
        active = get_active_object()
        armature = None
        for obj in bpy.context.selected_objects:
            if obj.type == 'ARMATURE':
                armature = obj
            if obj.type != 'MESH':
                continue
            
            # create tmp object

            #bpy.ops.object.duplicate()
            tmp = obj.copy()
            #tmp = get_active_object()
            tmp.data = obj.data.copy()
            tmp.name = '{}.tmp.VHDSOSB'.format(obj.name)
            if IS_LEGACY:
                bpy.context.scene.objects.link(tmp)
            else:
                bpy.context.scene.collection.objects.link(tmp)
            set_active_object(tmp)
            # tmpobjのshapekey消すならここ
            # 選択オブジェクトの差し替え
            select(obj, False)
            select(tmp, True)
            prop = bpy.context.scene.vhdsosb_selected_objects.add()
            prop.source = obj
            prop.copy = tmp

            # apply mirror modifier
            for mod in tmp.modifiers:
                if mod.type != 'MIRROR':
                    continue
                bpy.ops.object.modifier_apply(modifier=mod.name)
        set_active_object(armature)

        return {'FINISHED'}


class VHDSOnlySelectedBonesOperator(bpy.types.Operator):
    bl_idname = "wm.voxel_heat_diffuse_only_selected_bones"
    bl_label = "Voxel Heat Diffuse Skinning (Only selected bones)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        restore = []

        if 'voxel_heat_diffuse' not in dir(bpy.ops.wm):
            return {'FINISHED'}

        armature = None

        # get selected armature object
        for obj in bpy.context.selected_objects:
            if obj.type == 'ARMATURE':
                armature = obj
                break
        if not armature:
            return {'FINISHED'}

        # remove vertex weight
        if context.scene.vhdsosb_remove_vertex_weight:
            for obj in bpy.context.selected_objects:
                if obj.type == 'MESH':
                    if context.scene.voxel_protect:
                        unselected = [v for v in obj.data.vertices if not v.select]
                        for v in unselected:
                            for i, group in enumerate(v.groups):
                                v.groups[i].weight = 0
                    else:
                        for vertex_group in obj.vertex_groups:
                            obj.vertex_groups.remove(vertex_group)

        # change use_deform
        for bone in armature.data.bones:
            restore.append((bone.name, bone.use_deform))
            if bone.select:
                bone.use_deform = True
            else:
                bone.use_deform = False 

        # exec voxel heat deffuse skinning
        bpy.ops.wm.voxel_heat_diffuse()

        # restore use_deform
        for (bone_name, use_deform) in restore:
            armature.data.bones[bone_name].use_deform = use_deform

        return {'FINISHED'}


class VHDSOnlySelectedBonesPostprocessOperator(bpy.types.Operator):
    bl_idname = "wm.voxel_heat_diffuse_only_selected_bones_postprocess"
    bl_label = "Post-process"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected_objects = bpy.context.scene.vhdsosb_selected_objects
        active = get_active_object()
        for item in selected_objects:
            obj = item.source
            tmp = item.copy
            set_active_object(obj)

            # copy vertex weights from tmp object
            mod = obj.modifiers.new(name="tmp_data_transfer", type='DATA_TRANSFER')
            mod.object = tmp
            mod.use_vert_data = True
            mod.data_types_verts = {'VGROUP_WEIGHTS'}
            bpy.ops.object.datalayout_transfer(modifier=mod.name)
            bpy.ops.object.modifier_apply(modifier=mod.name)

            select(obj, True)
            for scene in bpy.data.scenes:
                if IS_LEGACY:
                    scene.objects.unlink(tmp)
                else:
                    scene.collection.objects.unlink(tmp)
        bpy.context.scene.vhdsosb_selected_objects.clear()
        set_active_object(active)

        return {'FINISHED'}

        
bpy.types.Scene.vhdsosb_remove_vertex_weight = bpy.props.BoolProperty(
    name="処理前に対象オブジェクトの頂点ウェイトを削除",
    default=True,
    description="処理前に対象オブジェクトの頂点ウェイトを削除",
)


class VHDSOSBSelectedItem(bpy.types.PropertyGroup):
    source = bpy.props.PointerProperty(type=bpy.types.Object)
    copy = bpy.props.PointerProperty(type=bpy.types.Object)


class VHDSOSBPanel(bpy.types.Panel):
    bl_label = "Voxel Heat Diffuse Skinning"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS' if IS_LEGACY else 'UI'
    bl_category = 'Animation' if IS_LEGACY else 'Mesh Online'

    @classmethod
    def poll(self, context):
        arm_count = 0
        obj_count = 0
        for ob in bpy.context.selected_objects:
            if 'ARMATURE' == ob.type:
                arm_count += 1
            if 'MESH' == ob.type:
                obj_count += 1
        return (context.mode == 'OBJECT' and arm_count == 1 and obj_count >= 1 and 'voxel_heat_diffuse' in dir(bpy.ops.wm))
    
    def draw(self, context):
        layout = self.layout
        ##　出現条件とか選択ボーンとかわかるようにする
        row = layout.row()
        row.prop(context.scene, 'vhdsosb_remove_vertex_weight')
        row = layout.row()
        row.operator(VHDSOnlySelectedBonesPrepareOperator.bl_idname)
        row = layout.row()
        row.operator(VHDSOnlySelectedBonesOperator.bl_idname)
        if len(bpy.context.scene.vhdsosb_selected_objects.items()) > 0:
            row = layout.row()
            row.operator(VHDSOnlySelectedBonesPostprocessOperator.bl_idname)


classesToRegister = [
    VHDSOnlySelectedBonesOperator,
    VHDSOnlySelectedBonesPrepareOperator,
    VHDSOnlySelectedBonesPostprocessOperator,
    VHDSOSBPanel,
    VHDSOSBSelectedItem
]


def register():
    for value in classesToRegister:
        bpy.utils.register_class(value)
    bpy.types.Scene.vhdsosb_selected_objects = bpy.props.CollectionProperty(type=VHDSOSBSelectedItem)


def unregister():
    for value in classesToRegister:
        bpy.utils.unregister_class(value)
    if bpy.context.scene.get("vhdsosb_remove_vertex_weight"):
        del bpy.context.scene["vhdsosb_remove_vertex_weight"]
    if bpy.context.scene.get("vhdsosb_selected_objects"):
        del bpy.context.scene["vhdsosb_selected_objects"]

if __name__ == '__main__':
    register()

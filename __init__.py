bl_info = {
    "name": "Voxel Heat Diffuse Skinning - Only selected bones",
    "author": "Taremin",
    "version": (0, 0),
    "blender": (2, 79, 0),
    "location": "View3D > Tools > Animation",
    "description": "Voxel Heat Diffuse Skinning - Only selected bones",
    "warning": "",
    "category": "Object"
}

import bpy

class VHDSOnlySelectedBonesOperator(bpy.types.Operator):
    bl_idname = "wm.voxel_heat_diffuse_only_selected_bones"
    bl_label = "Voxel Heat Diffuse Skinning (Only selected bones)"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        restore = []

        if not 'voxel_heat_diffuse' in dir(bpy.ops.wm):
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
                    for vertex_group in obj.vertex_groups:
                        obj.vertex_groups.remove(vertex_group)

        # change use_deform
        for bone in armature.data.bones:
            restore.append((bone, bone.use_deform))
            if bone.select:
                bone.use_deform = True
            else:
                bone.use_deform = False 

        # exec voxel heat deffuse skinning
        bpy.ops.wm.voxel_heat_diffuse()

        # restore use_deform
        for (bone, use_deform) in restore:
            bone.use_deform = use_deform

        return {'FINISHED'}

        

bpy.types.Scene.vhdsosb_remove_vertex_weight = bpy.props.BoolProperty(
    name="処理前に対象オブジェクトの頂点ウェイトを削除",
    default=True,
    description="処理前に対象オブジェクトの頂点ウェイトを削除",
)

class VHDSOSBPanel(bpy.types.Panel):
    bl_label = "Voxel Heat Diffuse Skinning"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = 'Animation'

    @classmethod
    def poll(self, context):
        arm_count = 0
        obj_count = 0
        for ob in bpy.context.selected_objects:
            if 'ARMATURE' == ob.type:
                arm_count += 1
            if 'MESH' == ob.type:
                obj_count += 1
        return (context.mode == 'OBJECT' and arm_count == 1 and obj_count >= 1 and 'voxel_heat_diffuse' in dir(bpy.ops.wm) )
    
    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.prop(context.scene, 'vhdsosb_remove_vertex_weight')
        row = layout.row()
        row.operator("wm.voxel_heat_diffuse_only_selected_bones")

classesToRegister = [
    VHDSOnlySelectedBonesOperator,
    VHDSOSBPanel,
]

def register():
    for value in classesToRegister:
        bpy.utils.register_class(value)


def unregister():
    for value in classesToRegister:
        bpy.utils.unregister_class(value)

if __name__ == '__main__':
    register()

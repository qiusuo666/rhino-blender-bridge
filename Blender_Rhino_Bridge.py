bl_info = {
    "name": "Blender to Rhino 8 Bridge",
    "author": "AI Assistant",
    "version": (1, 2, 0),
    "blender": (5, 0, 0),
    "location": "View3D > Sidebar (N) > Rhino",
    "description": "Send and receive between Blender 5.x and Rhino 8 — OBJ/STL, independent objects, auto post-process",
    "category": "Import-Export",
}

import bpy
import os
import tempfile
import json
import glob as glob_module
import bmesh

TEMP_DIR = tempfile.gettempdir()
TEMP_FILE_OBJ = os.path.join(TEMP_DIR, "blender_rhino_exchange.obj")
TEMP_FILE_STL = os.path.join(TEMP_DIR, "blender_rhino_exchange.stl")
MANIFEST_OBJ = os.path.join(TEMP_DIR, "br_exchange_manifest.json")
MANIFEST_STL = os.path.join(TEMP_DIR, "br_exchange_manifest_stl.json")

# ---- 后处理参数 ----
MERGE_DISTANCE = 0.0001       # 合并重叠顶点的距离阈值
AUTO_SMOOTH_ANGLE = 0.523599  # 自动锐边角度（弧度，30°）

# ---- 坐标轴转换（Rhino Z-up ↔ Blender Y-up）----
FORWARD = 'NEGATIVE_Z'
UP = 'Y'


# ============================================================
#  后处理：合并重叠顶点 + 平滑着色 + 自动锐边
# ============================================================
def post_process_mesh(obj):
    """对导入的 mesh 对象进行后处理，使其立即可用"""
    if obj.type != 'MESH':
        return

    mesh = obj.data
    bpy.context.view_layer.objects.active = obj

    # 1. 合并重叠顶点（使用 BMesh，跨所有 Blender 版本兼容）
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(mesh)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=MERGE_DISTANCE)
    bmesh.update_edit_mesh(mesh)
    bpy.ops.object.mode_set(mode='OBJECT')

    # 2. 平滑着色 + 自动锐边
    bpy.ops.object.shade_smooth()
    mesh.use_auto_smooth = True
    mesh.auto_smooth_angle = AUTO_SMOOTH_ANGLE


# ============================================================
#  格式属性（场景级别，Blender 重启后持久化）
# ============================================================
def get_format_items():
    return [('OBJ', 'OBJ', '通用格式，保留材质'), ('STL', 'STL', '三角面片，着色更可靠')]


# ============================================================
#  发送到 Rhino
# ============================================================
class BR_OT_SendToRhino(bpy.types.Operator):
    bl_idname = "br.send_to_rhino"
    bl_label = "发送到 Rhino"
    bl_description = "将选中的物体以当前格式导出到 Rhino"

    def execute(self, context):
        if not context.selected_objects:
            self.report({'WARNING'}, "请先选择要发送的物体！")
            return {'CANCELLED'}

        fmt = context.scene.br_format

        if fmt == 'STL':
            bpy.ops.wm.stl_export(
                filepath=TEMP_FILE_STL,
                export_selected=True,
                forward_axis=FORWARD,
                up_axis=UP,
            )
        else:
            bpy.ops.wm.obj_export(
                filepath=TEMP_FILE_OBJ,
                export_selected_objects=True,
                forward_axis=FORWARD,
                up_axis=UP,
            )

        self.report({'INFO'}, "成功发送到 Rhino！（{}）".format(fmt))
        return {'FINISHED'}


# ============================================================
#  从 Rhino 接收 —— 按清单逐个导入，保持物体独立
# ============================================================
class BR_OT_GetFromRhino(bpy.types.Operator):
    bl_idname = "br.get_from_rhino"
    bl_label = "从 Rhino 接收"
    bl_description = "导入来自 Rhino 的物体（每个 Rhino 物体独立）"

    def _import_obj(self, manifest, prefix, ext, count, names):
        """逐个导入 OBJ 文件"""
        all_imported = []
        for i in range(count):
            fpath = os.path.join(TEMP_DIR, "{}_{}.{}".format(prefix, i, ext))
            if not os.path.exists(fpath):
                self.report({'WARNING'}, "缺少文件: {}_{}.{}".format(prefix, i, ext))
                continue

            bpy.ops.wm.obj_import(
                filepath=fpath,
                forward_axis=FORWARD,
                up_axis=UP,
            )
            for obj in bpy.context.selected_objects:
                post_process_mesh(obj)
                if i < len(names):
                    obj.name = names[i]
                all_imported.append(obj)
        return all_imported

    def _import_stl(self, manifest, prefix, ext, count, names):
        """逐个导入 STL 文件"""
        all_imported = []
        for i in range(count):
            fpath = os.path.join(TEMP_DIR, "{}_{}.{}".format(prefix, i, ext))
            if not os.path.exists(fpath):
                self.report({'WARNING'}, "缺少文件: {}_{}.{}".format(prefix, i, ext))
                continue

            bpy.ops.wm.stl_import(
                filepath=fpath,
                forward_axis=FORWARD,
                up_axis=UP,
            )
            for obj in bpy.context.selected_objects:
                post_process_mesh(obj)
                if i < len(names):
                    obj.name = names[i]
                all_imported.append(obj)
        return all_imported

    def execute(self, context):
        fmt = context.scene.br_format

        # ---- 逐文件清单模式 ----
        if fmt == 'STL':
            manifest_file = MANIFEST_STL
            prefix = "br_exchange_stl"
            ext = "stl"
            import_fn = self._import_stl
        else:
            manifest_file = MANIFEST_OBJ
            prefix = "br_exchange"
            ext = "obj"
            import_fn = self._import_obj

        if os.path.exists(manifest_file):
            with open(manifest_file, 'r', encoding='utf-8') as f:
                manifest = json.load(f)

            count = manifest.get("count", 0)
            names = manifest.get("names", [])
            all_imported = import_fn(manifest, prefix, ext, count, names)

            if all_imported:
                bpy.ops.object.select_all(action='DESELECT')
                for obj in all_imported:
                    obj.select_set(True)
                bpy.context.view_layer.objects.active = all_imported[0]

            self.report({'INFO'}, "成功导入 {} 个物体！（{}）".format(count, fmt))
            return {'FINISHED'}

        # ---- 回退：旧版单文件 ----
        fallback = TEMP_FILE_STL if fmt == 'STL' else TEMP_FILE_OBJ
        if os.path.exists(fallback):
            if fmt == 'STL':
                bpy.ops.wm.stl_import(filepath=fallback, forward_axis=FORWARD, up_axis=UP)
            else:
                bpy.ops.wm.obj_import(filepath=fallback, forward_axis=FORWARD, up_axis=UP)
            for obj in bpy.context.selected_objects:
                post_process_mesh(obj)
            self.report({'INFO'}, "成功从 Rhino 接收物体！（旧版 {}）".format(fmt))
            return {'FINISHED'}

        self.report({'WARNING'}, "未找到来自 Rhino 的数据！")
        return {'CANCELLED'}


# ============================================================
#  UI 面板
# ============================================================
class BR_PT_Panel(bpy.types.Panel):
    bl_label = "Rhino 桥接"
    bl_idname = "BR_PT_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Rhino'

    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene, "br_format", text="格式")
        layout.separator()
        row = layout.row(align=True)
        row.operator(BR_OT_SendToRhino.bl_idname, icon='EXPORT', text="发送")
        row.operator(BR_OT_GetFromRhino.bl_idname, icon='IMPORT', text="接收")


def register():
    bpy.types.Scene.br_format = bpy.props.EnumProperty(
        name="格式",
        items=get_format_items(),
        default='OBJ',
    )
    bpy.utils.register_class(BR_OT_SendToRhino)
    bpy.utils.register_class(BR_OT_GetFromRhino)
    bpy.utils.register_class(BR_PT_Panel)


def unregister():
    del bpy.types.Scene.br_format
    bpy.utils.unregister_class(BR_PT_Panel)
    bpy.utils.unregister_class(BR_OT_GetFromRhino)
    bpy.utils.unregister_class(BR_OT_SendToRhino)


if __name__ == "__main__":
    register()

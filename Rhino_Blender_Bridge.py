#! python 2
# -*- coding: utf-8 -*-
import rhinoscriptsyntax as rs
import os
import tempfile
import json
import glob as glob_module

TEMP_DIR = tempfile.gettempdir()
MANIFEST_OBJ = os.path.join(TEMP_DIR, "br_exchange_manifest.json")
MANIFEST_STL = os.path.join(TEMP_DIR, "br_exchange_manifest_stl.json")
TEMP_OBJ = os.path.join(TEMP_DIR, "blender_rhino_exchange.obj")
TEMP_STL = os.path.join(TEMP_DIR, "blender_rhino_exchange.stl")


def do_export(fmt, objs):
    """导出已选中的物体列表到 Blender（OBJ 或 STL）"""
    ext = "stl" if fmt == "STL" else "obj"
    prefix = "br_exchange_stl" if fmt == "STL" else "br_exchange"
    manifest_file = MANIFEST_STL if fmt == "STL" else MANIFEST_OBJ

    # ---------- 清理旧文件 ----------
    for f in glob_module.glob(os.path.join(TEMP_DIR, prefix + "_*." + ext)):
        try:
            os.remove(f)
        except Exception:
            pass
    if os.path.exists(manifest_file):
        try:
            os.remove(manifest_file)
        except Exception:
            pass

    # ---------- 逐个导出 ----------
    count = 0
    names = []
    for obj in objs:
        rs.UnselectAllObjects()
        rs.SelectObject(obj)
        fpath = os.path.join(TEMP_DIR, "{}_{}.{}".format(prefix, count, ext))
        cmd = '-_Export ' + chr(34) + fpath + chr(34) + ' _Enter _Enter _Enter'
        rs.Command(cmd, False)

        name = rs.ObjectName(obj)
        if not name:
            name = "Rhino_Object_{}".format(count + 1)
        names.append(name)
        count += 1

    manifest = {"count": count, "names": names}
    with open(manifest_file, 'w') as f:
        json.dump(manifest, f)

    print("成功发送 {} 个物体到 Blender！（{}）".format(count, fmt))


def send_to_blender(fmt):
    """选物体 → 导出"""
    objs = rs.SelectedObjects()
    if not objs:
        objs = rs.GetObjects("选择要发送到 Blender 的物体")
    if not objs:
        return
    do_export(fmt, objs)


def get_from_blender():
    """自动检测并导入 Blender 发来的 OBJ 或 STL"""
    if os.path.exists(TEMP_STL):
        cmd = '-_Import ' + chr(34) + TEMP_STL + chr(34) + ' _Enter _Enter'
        rs.Command(cmd, False)
        print("成功从 Blender 接收物体！（STL）")
        return

    if os.path.exists(TEMP_OBJ):
        cmd = '-_Import ' + chr(34) + TEMP_OBJ + chr(34) + ' _Enter _Enter'
        rs.Command(cmd, False)
        print("成功从 Blender 接收物体！（OBJ）")
        return

    print("未找到来自 Blender 的数据！")


if __name__ == "__main__":
    # 第一层：Send / Receive（左右键各一个）
    result = rs.GetString("选择操作", "Send", ["Send", "Receive"])

    if result is None or result == "":
        print("已取消。")

    elif result == "Send":
        # 第二层：Mesh / OBJ / STL
        sub = rs.GetString("Send 方式", "OBJ", ["Mesh", "OBJ", "STL"])

        if sub is None or sub == "":
            print("已取消。")

        elif sub == "Mesh":
            # 曲面转网格：调精度 → 自动选中转换后的网格
            before = set(rs.AllObjects())
            rs.Command('!_Mesh', False)
            after = set(rs.AllObjects())

            # 找出新创建的网格对象
            new_guids = list(after - before)
            mesh_objs = [g for g in new_guids if rs.IsMesh(g)]

            if not mesh_objs:
                print("未生成网格（可能取消了 Mesh 操作），导出中止。")
            else:
                rs.UnselectAllObjects()
                rs.SelectObjects(mesh_objs)
                print("已选中 {} 个新网格。".format(len(mesh_objs)))

                # 转完网格后继续选格式导出
                fmt = rs.GetString("选择导出格式", "OBJ", ["OBJ", "STL"])
                if fmt is None or fmt == "":
                    print("已取消。")
                else:
                    do_export(fmt, mesh_objs)

        elif sub in ("OBJ", "STL"):
            send_to_blender(sub)

    elif result == "Receive":
        get_from_blender()

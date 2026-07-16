# Rhino ↔ Blender Bridge

Blender 5.x 与 Rhino 8 双向模型传输插件，通过临时文件交换 OBJ/STL，一键发送/接收。

## 文件

| 文件 | 用途 |
|------|------|
| `Blender_Rhino_Bridge.py` | Blender 5.x 插件，安装后在侧边栏 N → Rhino 面板操作 |
| `Rhino_Blender_Bridge.py` | Rhino 8 脚本，交互菜单：Send / Receive |

## 安装

**Blender**：偏好设置 → 插件 → 安装 → 选 `Blender_Rhino_Bridge.py` → 搜索 "Rhino" 启用  
**Rhino**：拖入 `Rhino_Blender_Bridge.py` 到视口运行，或用 `RunPythonScript` 加载

## 使用

- **Blender → Rhino**：选中物体 → 点 **发送** → 切 Rhino → **Receive**
- **Rhino → Blender**：选物体 → **Send**（可选 Mesh 转网格 / OBJ / STL）→ 切 Blender → 点 **接收**

## 特性

- OBJ（保留材质）/ STL（三角面片）双格式
- Rhino 逐个导出，Blender 逐个导入，保持物体独立
- Blender 端自动后处理：合并重叠顶点、平滑着色、30° 锐边
- Rhino Z-up ↔ Blender Y-up 坐标轴自动转换
- Rhino Send → Mesh 模式：曲面自动转网格后导出

## 许可证

[GPL-2.0](LICENSE) — 与 Blender 相同。

# Rhino ↔ Blender Bridge

Blender 5.x 与 Rhino 8 之间的双向模型传输桥接插件。通过临时文件交换 OBJ/STL，一键发送/接收。

## 功能

- **双向传输**：Blender → Rhino、Rhino → Blender
- **格式支持**：OBJ（保留材质）/ STL（三角面片，着色更可靠）
- **独立物体**：Rhino 端逐个导出，Blender 端逐个导入，保持物体独立性
- **自动后处理（Blender 端）**：合并重叠顶点 + 平滑着色 + 自动锐边
- **坐标轴转换**：自动处理 Rhino Z-up ↔ Blender Y-up
- **Rhino Mesh 模式**：曲面自动转网格后再导出

## 文件

| 文件 | 说明 |
|------|------|
| `Blender_Rhino_Bridge.py` | Blender 5.x 插件，安装后在侧边栏（N → Rhino）操作 |
| `Rhino_Blender_Bridge.py` | Rhino 8 脚本，交互菜单：Send（Mesh/OBJ/STL）/ Receive |

## 安装

### Blender 端

1. Blender → 编辑 → 偏好设置 → 插件 → 安装
2. 选择 `Blender_Rhino_Bridge.py`
3. 搜索 "Rhino" 启用
4. 3D 视图按 N → "Rhino" 面板

> 要求：**Blender 5.0+**

### Rhino 端

拖入 `Rhino_Blender_Bridge.py` 到 Rhino 视口运行，或用 `RunPythonScript` 加载：
- **Send** → Mesh（曲面转网格）/ OBJ / STL
- **Receive** → 自动检测并导入

> 要求：**Rhino 8**

## 使用

1. Blender 选中物体 → 点击 **发送**
2. 切到 Rhino → 运行脚本 → **Receive**
3. 反向同理：Rhino 选物体 → **Send** → Blender 点 **接收**

## 技术细节

- 通过系统临时目录（`%TEMP%`）交换文件
- Blender 导入后自动：合并重叠顶点（0.0001）、平滑着色、30° 锐边
- Rhino 导出前自动 `UnselectAllObjects` 避免叠加选择
- STL 导出精度受 Rhino 文档渲染网格设置（MaxAngle 等）控制

## 许可证

[GNU General Public License v2.0](LICENSE) — 与 Blender 相同。

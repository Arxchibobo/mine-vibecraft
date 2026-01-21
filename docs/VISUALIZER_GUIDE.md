# VibeCraft Claude Code Visualizer

将 Claude Code 的工作流程在 Minecraft 中 3D 可视化！

## 概述

VibeCraft Visualizer 是一个将 Claude Code 的活动实时映射到 Minecraft 世界的可视化系统。它创建一个完整的 3D 控制室，显示：

- **Skills Matrix (技能矩阵)**: 9x9 网格展示 81 个技能
- **MCP Tower (MCP 塔)**: 垂直塔楼展示 MCP 服务器和工具
- **Plugins Garden (插件花园)**: 有机树形布局展示插件
- **Agent Timeline (代理时间线)**: 铁轨时间线展示任务进度
- **Central Hub (中央枢纽)**: 主控台展示会话统计

## 快速开始

### 1. 启动 VibeCraft MCP 服务器

```bash
cd mcp-server
uv run python -m src.vibecraft.server
```

### 2. 配置 Claude Code Hooks（可选）

将以下配置添加到 `~/.claude/hooks.json` 以启用实时事件推送：

**Unix/macOS:**
```json
{
  "version": "1.0",
  "description": "VibeCraft Visualizer hooks",
  "hooks": {
    "PostToolUse": [
      {
        "type": "command",
        "command": "curl -s -X POST http://localhost:8767/event -H 'Content-Type: application/json' -d '{\"event_type\": \"tool_call\", \"payload\": {\"tool\": \"$TOOL_NAME\"}}'",
        "background": true,
        "timeout": 5000
      }
    ],
    "PreSkillUse": [
      {
        "type": "command",
        "command": "curl -s -X POST http://localhost:8767/event -H 'Content-Type: application/json' -d '{\"event_type\": \"skill_invoke\", \"payload\": {\"skill\": \"$SKILL_NAME\"}}'",
        "background": true,
        "timeout": 5000
      }
    ],
    "PostSkillUse": [
      {
        "type": "command",
        "command": "curl -s -X POST http://localhost:8767/event -H 'Content-Type: application/json' -d '{\"event_type\": \"skill_complete\", \"payload\": {\"skill\": \"$SKILL_NAME\"}}'",
        "background": true,
        "timeout": 5000
      }
    ]
  }
}
```

**Windows PowerShell:**
```json
{
  "version": "1.0",
  "hooks": {
    "PostToolUse": [
      {
        "type": "command",
        "command": "powershell -Command \"Invoke-RestMethod -Uri 'http://localhost:8767/event' -Method Post -ContentType 'application/json' -Body '{\\\"event_type\\\": \\\"tool_call\\\", \\\"payload\\\": {\\\"tool\\\": \\\"$TOOL_NAME\\\"}}'\"",
        "background": true
      }
    ]
  }
}
```

### 3. 初始化可视化控制室

在 Minecraft 中，让 Claude 执行：

```
使用 visualizer_init 工具，参数:
{
  "layout": "full"
}
```

这将在玩家当前位置创建完整的 3D 可视化控制室。

## MCP 工具参考

### visualizer_init

初始化可视化控制室。

```json
{
  "layout": "full",      // "full" | "compact" | "minimal"
  "center": [100, 64, 100]  // 可选，默认为玩家位置
}
```

**布局模式:**
- `full`: 所有 5 个模块（推荐首次使用）
- `compact`: Hub + Timeline
- `minimal`: 仅 Hub

### visualizer_update

更新特定模块。

```json
{
  "module": "timeline",  // "skills" | "mcp" | "plugins" | "timeline" | "hub"
  "data": {
    "todos": [
      {"id": "1", "content": "Fix bug", "status": "completed"},
      {"id": "2", "content": "Write tests", "status": "in_progress"}
    ]
  }
}
```

### visualizer_highlight

高亮特定元素。

```json
{
  "type": "skill",     // "skill" | "mcp_server" | "mcp_tool" | "plugin"
  "name": "commit",
  "duration": 5        // 秒
}
```

### visualizer_query

查询可视化状态。

```json
{
  "what": "active_elements"  // "layout" | "active_elements" | "session" | "todos" | "all"
}
```

### visualizer_event

处理 Claude Code 事件（主要由 hooks 自动调用）。

```json
{
  "event_type": "tool_call",  // "tool_call" | "skill_invoke" | "agent_spawn" | "todo_update" | "error"
  "payload": {
    "tool": "execute_sql",
    "server": "supabase"
  }
}
```

## 模块详解

### Skills Matrix (技能矩阵)

位置：北侧 (z-40)

```
  ┌─────────────────────────────────────┐
  │  ■ ■ ■ ■ ■ ■ ■ ■ ■  (Layer 9)      │
  │  ■ ■ ■ ■ ■ ■ ■ ■ ■  (Layer 8)      │
  │  ...                               │
  │  ■ ■ ■ ■ ■ ■ ■ ■ ■  (Layer 1)      │
  └─────────────────────────────────────┘
```

方块含义：
- `sea_lantern`: 可用技能
- `glowstone`: 正在使用的技能
- `diamond_block`: 最近使用的技能
- `gray_concrete`: 不可用

### MCP Tower (MCP 塔)

位置：东侧 (x+40)

```
      ╔═════╗  <- Server 8
      ║ ●●● ║  <- Tools ring
      ╠═════╣
      ║ ●●● ║  <- Server 7
      ╠═════╣
      ...
      ╚═════╝  <- Base
```

方块含义：
- 塔核心：服务器状态
  - `emerald_block`: 在线
  - `redstone_block`: 离线
  - `gold_block`: 重连中
- 工具环：围绕塔核心的工具
  - `iron_block`: 可用工具
  - `lapis_block`: 最近使用
  - `coal_block`: 不可用

### Plugins Garden (插件花园)

位置：西侧 (x-40)

```
      🌳  🌲    🌴
        🌳    🌲
      🌴    🌳
```

每棵树代表一个插件：
- 树高 = 复杂度（agents + skills 数量）
- 叶子颜色 = 类别
  - `oak_leaves`: 开发类
  - `birch_leaves`: 基础设施类
  - `spruce_leaves`: 测试类
  - `azalea_leaves`: AI 类

### Agent Timeline (代理时间线)

位置：南侧 (z+30)

```
START ═══╦═══╦═══╦═══╦═══╦═══╦═══ END
         ║   ║   ║   ║   ║   ║
        [T1][T2][🚃][T4][..][..]
         ✓   ✓   ⏳   ○   ○   ○
```

方块含义：
- `emerald_block`: 已完成任务 ✓
- `gold_block`: 当前任务 (矿车位置)
- `iron_block`: 待执行任务
- `redstone_block`: 失败任务

### Central Hub (中央枢纽)

位置：中心

```
        ┌───────────────────┐
        │   SESSION STATS   │
        │  Tool Calls: 42   │
        │  Agents: 3        │
        │  Progress: 75%    │
        └───────────────────┘
              ╔═══╗
              ║ ● ║  <- 状态核心
              ╚═══╝
```

显示内容：
- 会话时长
- 工具调用次数
- Agent 生成数
- 任务完成进度
- 错误计数

## 自定义数据目录

可视化数据存储在 `mcp-server/src/vibecraft/visualizer/data/` 目录：

- `skills_catalog.json`: 技能目录
- `mcp_registry.json`: MCP 服务器注册表
- `plugins_manifest.json`: 插件清单

可以修改这些文件来自定义显示的内容。

## 故障排除

### 控制室没有出现

1. 确保 Minecraft 客户端已连接
2. 确保玩家在线（WorldEdit 需要玩家上下文）
3. 检查 VibeCraft 日志：`mcp-server/logs/`

### 实时更新不工作

1. 检查 hooks.json 是否正确配置
2. 确保 HTTP 服务器在端口 8767 运行
3. 测试 curl 命令是否正常

### 方块没有正确渲染

1. 确保使用的是 Minecraft 1.20+
2. 检查 WorldEdit 是否正确安装
3. 验证玩家有 WorldEdit 权限

## 扩展开发

### 添加新的可视化模块

1. 在 `visualizer/layouts/` 创建新的布局类
2. 实现 `render_full()` 方法
3. 在 `visualizer_tools.py` 中注册
4. 更新 `tool_schemas.py` 添加 schema

### 添加新的事件类型

1. 在 `state.py` 添加事件处理方法
2. 在 `event_receiver.py` 添加路由
3. 更新 hooks.json 配置
4. 在 `visualizer_event` 工具中添加处理逻辑

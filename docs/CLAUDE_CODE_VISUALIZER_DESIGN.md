# Claude Code 3D Visualizer - VibeCraft Extension

> **目标**: 把 Minecraft 变成 Claude Code 的实时 3D 控制室，展示 Skills、MCP、Plugins 和 Agent 进度

---

## 核心概念

```
┌────────────────────────────────────────────────────────────────┐
│                    Minecraft 3D 控制室                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │  Skills  │  │   MCP    │  │ Plugins  │  │  Agent   │       │
│  │  Matrix  │  │  Tower   │  │  Garden  │  │ Timeline │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
│                                                                │
│                    ┌─────────────────┐                         │
│                    │  Central Hub    │                         │
│                    │  (实时状态)     │                         │
│                    └─────────────────┘                         │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
               ┌──────────────────────────────┐
               │   VibeCraft MCP Server       │
               │   + Visualizer Extension     │
               └──────────────────────────────┘
                              │
                              ▼
               ┌──────────────────────────────┐
               │      Claude Code CLI         │
               │   (发送状态更新事件)          │
               └──────────────────────────────┘
```

---

## 模块设计

### 1. Skills Matrix (技能矩阵)

**概念**: 81 个 Skills 排列成 9x9 立体矩阵，每个技能用不同方块表示

```
Y=5  ┌───┬───┬───┬───┬───┬───┬───┬───┬───┐
     │ S │ S │ S │ S │ S │ S │ S │ S │ S │  Category: Backend
Y=4  ├───┼───┼───┼───┼───┼───┼───┼───┼───┤
     │ S │ S │ S │ S │ S │ S │ S │ S │ S │  Category: Frontend
Y=3  ├───┼───┼───┼───┼───┼───┼───┼───┼───┤
     │ S │ S │ S │ S │ S │ S │ S │ S │ S │  Category: DevOps
     └───┴───┴───┴───┴───┴───┴───┴───┴───┘
```

**方块映射**:
| 状态 | 方块 | 说明 |
|------|------|------|
| 可用 | `sea_lantern` | 发光，表示可用 |
| 活跃中 | `glowstone` + 粒子 | 正在执行 |
| 最近使用 | `diamond_block` | 10分钟内使用过 |
| 未安装 | `gray_concrete` | 灰色，不可用 |

**交互**:
- 玩家靠近时显示 Skill 名称 (Hologram)
- 点击方块触发 Skill 详情面板

---

### 2. MCP Tower (MCP 塔)

**概念**: 垂直塔楼，每层代表一个 MCP Server，工具围绕塔身排列

```
      ┌─────┐
      │ TOP │  ← 活跃连接指示器
      ├─────┤
   ┌──┤     ├──┐
   │T1│SUPABASE│T2│  ← MCP Server 层
   └──┤     ├──┘
      ├─────┤
   ┌──┤     ├──┐
   │T1│STRIPE│T2│    ← 工具环绕
   └──┤     ├──┘
      ├─────┤
      │BASE │
      └─────┘
```

**每层结构**:
- 中心: MCP Server 名称 (告示牌)
- 环绕: 该 Server 的工具 (按钮方块)
- 颜色: 连接状态 (绿=在线, 红=离线, 黄=重连中)

**MCP Servers 示例**:
| Server | 工具数 | 层级 |
|--------|--------|------|
| vibecraft | 46 | Layer 1 |
| supabase | 20+ | Layer 2 |
| stripe | 15+ | Layer 3 |
| playwright | 20+ | Layer 4 |
| asana | 30+ | Layer 5 |

---

### 3. Plugins Garden (插件花园)

**概念**: 有机花园布局，每个 Plugin 是一棵"功能树"

```
    🌳 backend-development     🌲 security-scanning
         /|\                        /|\
        / | \                      / | \
       T  T  T                    T  T  T
      (tools)                   (tools)
```

**树的表示**:
- 树干高度 = Plugin 复杂度
- 树叶颜色 = Plugin 类别
- 果实 = 子 Agent 类型

**类别颜色**:
| 类别 | 树叶颜色 |
|------|----------|
| Development | `oak_leaves` (绿) |
| Security | `spruce_leaves` (深绿) |
| Documentation | `birch_leaves` (浅黄) |
| Infrastructure | `jungle_leaves` (茂密) |
| AI/ML | `azalea_leaves` (粉) |

---

### 4. Agent Timeline (进度时间线)

**概念**: 铁轨时间线，矿车代表任务，实时移动

```
START ═══╦═══╦═══╦═══╦═══╦═══╦═══╦═══╦═══ END
         ║   ║   ║   ║   ║   ║   ║   ║
        [T1][T2][T3][▶ ][..][..][..][..]
         ✓   ✓   ⏳
```

**元素**:
| 元素 | Minecraft 表示 | 说明 |
|------|----------------|------|
| 已完成任务 | `emerald_block` + 勾 | 绿色 |
| 当前任务 | `minecart` 移动中 | 动态 |
| 待执行 | `iron_block` | 灰色 |
| 失败 | `redstone_block` | 红色 |

**实时更新**:
- TodoWrite 事件 → 更新时间线方块
- 任务完成 → 矿车前进
- 新增任务 → 延长轨道

---

### 5. Central Hub (中央枢纽)

**概念**: 圆形控制台，显示实时系统状态

```
         ╭─────────────────╮
        ╱                   ╲
       │   TOKEN USAGE      │  ← 实时 token 计数器
       │   ███████░░ 70%    │
       │                    │
       │   ACTIVE AGENTS: 3 │  ← 并行 agent 数
       │                    │
       │   SESSION TIME     │  ← 会话时长
       │   00:45:23         │
        ╲                   ╱
         ╰─────────────────╯
```

**显示内容**:
1. Token 使用量 (进度条)
2. 活跃 Agent 数量
3. 会话时长
4. 最近工具调用
5. 错误/警告计数

---

## 数据同步架构

### 事件流

```
┌─────────────┐     Events      ┌──────────────┐     Commands    ┌───────────┐
│ Claude Code │ ───────────────→│  Visualizer  │ ───────────────→│ Minecraft │
│    CLI      │                 │   Server     │                 │  World    │
└─────────────┘                 └──────────────┘                 └───────────┘
      │                               │                               │
      │  Hook: tool_call              │  WebSocket                    │
      │  Hook: agent_spawn            │  JSON-RPC                     │
      │  Hook: todo_update            │                               │
      │  Hook: error                  │                               │
      └──────────────────────────────→│                               │
                                      └──────────────────────────────→│
```

### Claude Code Hooks (新增)

```javascript
// ~/.claude/hooks.json
{
  "on_tool_call": {
    "command": "curl -X POST http://localhost:8766/event",
    "payload": {
      "type": "tool_call",
      "tool": "${tool_name}",
      "timestamp": "${timestamp}"
    }
  },
  "on_agent_spawn": {
    "command": "curl -X POST http://localhost:8766/event",
    "payload": {
      "type": "agent_spawn",
      "agent_type": "${agent_type}",
      "task": "${description}"
    }
  },
  "on_todo_update": {
    "command": "curl -X POST http://localhost:8766/event",
    "payload": {
      "type": "todo_update",
      "todos": "${todos_json}"
    }
  }
}
```

### Visualizer Server (新模块)

```python
# mcp-server/src/vibecraft/visualizer/
├── __init__.py
├── event_receiver.py      # HTTP 接收 Claude Code 事件
├── state_manager.py       # 维护当前状态
├── minecraft_renderer.py  # 生成 Minecraft 命令
└── layouts/
    ├── skills_matrix.py
    ├── mcp_tower.py
    ├── plugins_garden.py
    ├── agent_timeline.py
    └── central_hub.py
```

---

## 新增 MCP 工具

### 1. `visualizer_init`
初始化可视化控制室

```python
{
  "name": "visualizer_init",
  "description": "在玩家位置创建 3D 可视化控制室",
  "parameters": {
    "layout": "full | compact | minimal",
    "center": [x, y, z]  # 可选，默认玩家位置
  }
}
```

### 2. `visualizer_update`
手动更新可视化状态

```python
{
  "name": "visualizer_update",
  "description": "更新特定模块的显示",
  "parameters": {
    "module": "skills | mcp | plugins | timeline | hub",
    "data": { ... }
  }
}
```

### 3. `visualizer_highlight`
高亮特定元素

```python
{
  "name": "visualizer_highlight",
  "description": "高亮一个 skill/tool/plugin",
  "parameters": {
    "type": "skill | mcp_tool | plugin",
    "name": "commit",
    "duration": 5  # 秒
  }
}
```

### 4. `visualizer_query`
查询可视化状态

```python
{
  "name": "visualizer_query",
  "description": "获取当前可视化状态",
  "parameters": {
    "what": "layout | active_elements | recent_events"
  }
}
```

---

## 实现路线图

### Phase 1: 基础架构 (1-2 周)
- [ ] Visualizer Server 框架
- [ ] 事件接收 HTTP endpoint
- [ ] 状态管理器
- [ ] 基础渲染器 (方块放置)

### Phase 2: 核心模块 (2-3 周)
- [ ] Skills Matrix 布局算法
- [ ] MCP Tower 生成器
- [ ] Central Hub 仪表盘
- [ ] 实时更新机制

### Phase 3: 高级功能 (2-3 周)
- [ ] Plugins Garden (程序化树生成)
- [ ] Agent Timeline (动态轨道)
- [ ] 交互系统 (点击触发)
- [ ] 粒子效果和动画

### Phase 4: 集成测试 (1 周)
- [ ] Claude Code Hooks 配置
- [ ] 端到端测试
- [ ] 性能优化
- [ ] 文档和示例

---

## 技术挑战

### 1. 实时更新性能
**问题**: 频繁更新会导致卡顿
**方案**:
- 批量更新 (每 500ms 合并事件)
- 差量更新 (只改变的方块)
- 优先级队列 (重要事件优先)

### 2. 空间布局
**问题**: 81 Skills + 100+ MCP 工具 + 50+ Plugins 需要大量空间
**方案**:
- 分层设计 (Skills 地面层, MCP 塔楼, Plugins 花园)
- 可折叠/展开
- LOD (远处简化显示)

### 3. Claude Code 集成
**问题**: 需要 Claude Code 发送事件
**方案**:
- 利用现有 Hooks 系统
- 或扩展 MCP 协议添加事件通道

### 4. 状态持久化
**问题**: 重启后状态丢失
**方案**:
- 定期保存状态到 JSON
- Minecraft 结构保存 (NBT)

---

## 示例场景

### 场景 1: 开发会话开始

```
1. 玩家进入控制室
2. Central Hub 显示 "Session Started"
3. Skills Matrix 全部亮起 (可用状态)
4. MCP Tower 检查连接状态
5. Timeline 清空，准备接收任务
```

### 场景 2: 执行 /commit

```
1. Skills Matrix 中 "commit" 方块高亮 (glowstone)
2. Timeline 添加新任务方块
3. MCP Tower 中 "git" 相关工具闪烁
4. Central Hub 更新 tool_call 计数
5. 完成后 "commit" 恢复 sea_lantern
6. Timeline 任务变绿 (emerald_block)
```

### 场景 3: 并行 Agent 运行

```
1. 3 个 Agent 同时启动
2. Timeline 分叉成 3 条并行轨道
3. Central Hub 显示 "ACTIVE AGENTS: 3"
4. 每个 Agent 的任务独立推进
5. 完成后轨道合并
```

---

## 文件结构 (新增)

```
mcp-server/src/vibecraft/
├── visualizer/                    # 新模块
│   ├── __init__.py
│   ├── server.py                  # HTTP 事件服务器
│   ├── state.py                   # 状态管理
│   ├── renderer.py                # Minecraft 渲染
│   ├── layouts/
│   │   ├── skills_matrix.py
│   │   ├── mcp_tower.py
│   │   ├── plugins_garden.py
│   │   ├── agent_timeline.py
│   │   └── central_hub.py
│   └── data/
│       ├── skills_catalog.json    # 81 skills 数据
│       ├── mcp_registry.json      # MCP 工具注册
│       └── plugin_manifest.json   # Plugin 清单
│
├── tools/
│   └── visualizer_tools.py        # 4 个新 MCP 工具
│
└── server.py                      # 更新: 注册新工具
```

---

## 下一步行动

1. **确认设计方向** - 这个设计是否符合你的预期？
2. **优先级排序** - 哪个模块最重要？建议先做 Central Hub + Skills Matrix
3. **开始实现** - 从 Visualizer Server 框架开始

---

*这是一个宏大但可实现的项目。Minecraft 的可视化能力 + VibeCraft 的基础设施 = 独特的 AI 运维体验。*

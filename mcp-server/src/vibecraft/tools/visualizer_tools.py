"""
Visualizer MCP Tools

提供 4 个 MCP 工具用于控制 Claude Code 可视化:
1. visualizer_init - 初始化可视化控制室
2. visualizer_update - 更新特定模块
3. visualizer_highlight - 高亮特定元素
4. visualizer_query - 查询可视化状态
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from mcp.types import TextContent

if TYPE_CHECKING:
    from ..client_bridge import ClientBridge
    from ..config import VibeCraftConfig

from . import register_tool

logger = logging.getLogger(__name__)

# 全局 Visualizer 实例
_visualizer_instance = None


def get_visualizer():
    """获取或创建 Visualizer 实例"""
    global _visualizer_instance

    if _visualizer_instance is None:
        from ..visualizer import VisualizerState, MinecraftRenderer
        from ..visualizer.layouts import (
            SkillsMatrixLayout,
            MCPTowerLayout,
            PluginsGardenLayout,
            AgentTimelineLayout,
            CentralHubLayout,
        )

        data_dir = Path(__file__).parent.parent / "visualizer" / "data"

        state = VisualizerState(data_dir)
        renderer = MinecraftRenderer()

        _visualizer_instance = {
            "state": state,
            "renderer": renderer,
            "layouts": {
                "skills": SkillsMatrixLayout(renderer),
                "mcp": MCPTowerLayout(renderer),
                "plugins": PluginsGardenLayout(renderer),
                "timeline": AgentTimelineLayout(renderer),
                "hub": CentralHubLayout(renderer),
            },
        }

    return _visualizer_instance


async def execute_commands(
    client_bridge: "ClientBridge",
    commands: list[str],
) -> list[str]:
    """执行 Minecraft 命令列表"""
    results = []
    for cmd in commands:
        try:
            result = client_bridge.execute_command(cmd)
            results.append(result)
        except Exception as e:
            logger.error(f"Command failed: {cmd} - {e}")
            results.append(f"Error: {e}")
    return results


@register_tool("visualizer_init")
async def handle_visualizer_init(
    arguments: dict[str, Any],
    client_bridge: "ClientBridge",
    config: "VibeCraftConfig",
    logger: logging.Logger,
) -> list[TextContent]:
    """
    初始化可视化控制室

    在玩家位置创建完整的 3D 可视化控制室，包括:
    - Skills Matrix (技能矩阵)
    - MCP Tower (MCP 塔)
    - Plugins Garden (插件花园)
    - Agent Timeline (进度时间线)
    - Central Hub (中央枢纽)

    参数:
        layout: 布局模式 - "full" (完整), "compact" (紧凑), "minimal" (最小)
        center: 中心坐标 [x, y, z], 默认使用玩家位置
    """
    layout_mode = arguments.get("layout", "full")
    center = arguments.get("center")

    vis = get_visualizer()
    state = vis["state"]
    renderer = vis["renderer"]
    layouts = vis["layouts"]

    # 获取中心位置
    if center:
        cx, cy, cz = center
    else:
        # 从客户端获取玩家位置
        try:
            pos_result = client_bridge.execute_command("getpos")
            # 解析位置 (假设返回格式类似 "x=100, y=64, z=200")
            cx, cy, cz = 0, 64, 0  # 默认值
        except Exception:
            cx, cy, cz = 0, 64, 0

    state.center = (cx, cy, cz)
    state.layout_mode = layout_mode
    renderer.set_center(cx, cy, cz)

    from ..visualizer.renderer import Position
    center_pos = Position(cx, cy, cz)

    all_commands = []

    # 根据布局模式选择性渲染
    if layout_mode == "full":
        # 完整布局: 所有 5 个模块
        # Central Hub 在中心
        hub_commands = layouts["hub"].render_full(state, center_pos)
        all_commands.extend(hub_commands)

        # Skills Matrix 在北侧
        skills_center = center_pos.offset(0, 0, -40)
        skills_commands = layouts["skills"].render_full(state, skills_center)
        all_commands.extend(skills_commands)

        # MCP Tower 在东侧
        mcp_center = center_pos.offset(40, 0, 0)
        mcp_commands = layouts["mcp"].render_full(state, mcp_center)
        all_commands.extend(mcp_commands)

        # Plugins Garden 在西侧
        plugins_center = center_pos.offset(-40, 0, 0)
        plugins_commands = layouts["plugins"].render_full(state, plugins_center)
        all_commands.extend(plugins_commands)

        # Agent Timeline 在南侧
        timeline_center = center_pos.offset(0, 0, 30)
        timeline_commands = layouts["timeline"].render_full(state, timeline_center)
        all_commands.extend(timeline_commands)

    elif layout_mode == "compact":
        # 紧凑布局: Hub + Timeline
        hub_commands = layouts["hub"].render_full(state, center_pos)
        all_commands.extend(hub_commands)

        timeline_center = center_pos.offset(0, 0, 20)
        timeline_commands = layouts["timeline"].render_full(state, timeline_center)
        all_commands.extend(timeline_commands)

    else:  # minimal
        # 最小布局: 只有 Hub
        hub_commands = layouts["hub"].render_full(state, center_pos)
        all_commands.extend(hub_commands)

    # 执行命令
    results = await execute_commands(client_bridge, all_commands)

    return [
        TextContent(
            type="text",
            text=json.dumps({
                "success": True,
                "layout": layout_mode,
                "center": [cx, cy, cz],
                "modules_rendered": (
                    ["hub", "skills", "mcp", "plugins", "timeline"] if layout_mode == "full"
                    else ["hub", "timeline"] if layout_mode == "compact"
                    else ["hub"]
                ),
                "commands_executed": len(all_commands),
            }, indent=2),
        )
    ]


@register_tool("visualizer_update")
async def handle_visualizer_update(
    arguments: dict[str, Any],
    client_bridge: "ClientBridge",
    config: "VibeCraftConfig",
    logger: logging.Logger,
) -> list[TextContent]:
    """
    更新特定模块的显示

    参数:
        module: 要更新的模块 - "skills", "mcp", "plugins", "timeline", "hub"
        data: 可选的更新数据 (如果不提供则从状态自动更新)
    """
    module = arguments.get("module")
    data = arguments.get("data", {})

    if not module:
        return [
            TextContent(
                type="text",
                text=json.dumps({"success": False, "error": "Module not specified"}),
            )
        ]

    vis = get_visualizer()
    state = vis["state"]
    layouts = vis["layouts"]

    from ..visualizer.renderer import Position
    center_pos = Position(*state.center)

    commands = []

    if module == "skills":
        if data.get("skills"):
            # 更新特定 skills
            for skill_data in data["skills"]:
                skill_name = skill_data.get("name")
                if skill_name in state.skills:
                    state.handle_skill_invoke(skill_name) if skill_data.get("active") else None
                    commands.extend(layouts["skills"].render_skill(
                        state.skills[skill_name],
                        center_pos.offset(0, 0, -40),
                    ))
        else:
            # 更新整个 matrix
            commands.extend(layouts["skills"].render_full(state, center_pos.offset(0, 0, -40)))

    elif module == "mcp":
        if data.get("server"):
            server_name = data["server"]
            status = data.get("status", "online")
            state.handle_mcp_status(server_name, status)
            if server_name in state.mcp_servers:
                commands.extend(layouts["mcp"].render_server(
                    state.mcp_servers[server_name],
                    center_pos.offset(40, 0, 0),
                ))
        else:
            commands.extend(layouts["mcp"].render_full(state, center_pos.offset(40, 0, 0)))

    elif module == "plugins":
        commands.extend(layouts["plugins"].render_full(state, center_pos.offset(-40, 0, 0)))

    elif module == "timeline":
        if data.get("todos"):
            state.handle_todo_update(data["todos"])
        commands.extend(layouts["timeline"].render_tasks(state.todos, center_pos.offset(0, 0, 30)))

    elif module == "hub":
        commands.extend(layouts["hub"].render_update(state, center_pos))

    else:
        return [
            TextContent(
                type="text",
                text=json.dumps({"success": False, "error": f"Unknown module: {module}"}),
            )
        ]

    # 执行命令
    results = await execute_commands(client_bridge, commands)

    return [
        TextContent(
            type="text",
            text=json.dumps({
                "success": True,
                "module": module,
                "commands_executed": len(commands),
            }, indent=2),
        )
    ]


@register_tool("visualizer_highlight")
async def handle_visualizer_highlight(
    arguments: dict[str, Any],
    client_bridge: "ClientBridge",
    config: "VibeCraftConfig",
    logger: logging.Logger,
) -> list[TextContent]:
    """
    高亮特定元素

    参数:
        type: 元素类型 - "skill", "mcp_tool", "mcp_server", "plugin"
        name: 元素名称
        duration: 高亮持续时间 (秒), 默认 5
    """
    element_type = arguments.get("type")
    name = arguments.get("name")
    duration = arguments.get("duration", 5)

    if not element_type or not name:
        return [
            TextContent(
                type="text",
                text=json.dumps({"success": False, "error": "Type and name required"}),
            )
        ]

    vis = get_visualizer()
    layouts = vis["layouts"]

    commands = []

    if element_type == "skill":
        commands.extend(layouts["skills"].highlight_skill(name, duration))
    elif element_type == "mcp_server":
        commands.extend(layouts["mcp"].highlight_server(name, duration))
    elif element_type == "mcp_tool":
        commands.extend(layouts["mcp"].highlight_tool(name))
    elif element_type == "plugin":
        commands.extend(layouts["plugins"].highlight_plugin(name))
    else:
        return [
            TextContent(
                type="text",
                text=json.dumps({"success": False, "error": f"Unknown type: {element_type}"}),
            )
        ]

    # 执行命令
    results = await execute_commands(client_bridge, commands)

    return [
        TextContent(
            type="text",
            text=json.dumps({
                "success": True,
                "highlighted": {"type": element_type, "name": name},
                "duration": duration,
            }, indent=2),
        )
    ]


@register_tool("visualizer_query")
async def handle_visualizer_query(
    arguments: dict[str, Any],
    client_bridge: "ClientBridge",
    config: "VibeCraftConfig",
    logger: logging.Logger,
) -> list[TextContent]:
    """
    查询可视化状态

    参数:
        what: 查询内容 - "layout", "active_elements", "recent_events", "session", "all"
    """
    what = arguments.get("what", "all")

    vis = get_visualizer()
    state = vis["state"]

    result = {}

    if what in ("layout", "all"):
        result["layout"] = {
            "mode": state.layout_mode,
            "center": state.center,
        }

    if what in ("active_elements", "all"):
        result["active_elements"] = {
            "active_skills": [s.name for s in state.get_active_skills()],
            "recent_skills": [s.name for s in state.get_recent_skills()],
            "online_mcp_servers": [s.name for s in state.get_online_mcp_servers()],
            "active_agents": [a.id for a in state.get_active_agents()],
        }

    if what in ("session", "all"):
        result["session"] = {
            "duration": state.get_session_duration_formatted(),
            "tool_calls": state.session.tool_calls,
            "agent_spawns": state.session.agent_spawns,
            "tasks_completed": state.session.tasks_completed,
            "tasks_failed": state.session.tasks_failed,
            "errors": state.session.errors,
        }

    if what in ("recent_events", "all"):
        # 获取最近的脏数据
        dirty = state.get_dirty_modules()
        result["pending_updates"] = list(dirty.keys())

    if what == "todos":
        result["todos"] = [
            {
                "id": t.id,
                "content": t.content,
                "status": t.status.value,
            }
            for t in state.todos
        ]

    return [
        TextContent(
            type="text",
            text=json.dumps(result, indent=2),
        )
    ]


# ===== 事件处理工具 =====


@register_tool("visualizer_event")
async def handle_visualizer_event(
    arguments: dict[str, Any],
    client_bridge: "ClientBridge",
    config: "VibeCraftConfig",
    logger: logging.Logger,
) -> list[TextContent]:
    """
    处理 Claude Code 事件并更新可视化

    参数:
        event_type: 事件类型 - "tool_call", "skill_invoke", "agent_spawn", "todo_update", "error"
        payload: 事件数据
    """
    event_type = arguments.get("event_type")
    payload = arguments.get("payload", {})

    vis = get_visualizer()
    state = vis["state"]
    layouts = vis["layouts"]

    from ..visualizer.renderer import Position
    center_pos = Position(*state.center)

    commands = []

    if event_type == "tool_call":
        tool_name = payload.get("tool", "unknown")
        server = payload.get("server")
        state.handle_tool_call(tool_name, server)

        # 更新 Hub
        commands.extend(layouts["hub"].render_update(state, center_pos))

        # 如果有对应 MCP 工具，高亮它
        if server:
            commands.extend(layouts["mcp"].highlight_tool(tool_name))

    elif event_type == "skill_invoke":
        skill_name = payload.get("skill", "unknown")
        state.handle_skill_invoke(skill_name)

        # 更新 Skills Matrix 中的对应 skill
        if skill_name in state.skills:
            commands.extend(layouts["skills"].render_skill(
                state.skills[skill_name],
                center_pos.offset(0, 0, -40),
            ))

    elif event_type == "skill_complete":
        skill_name = payload.get("skill", "unknown")
        state.handle_skill_complete(skill_name)

        if skill_name in state.skills:
            commands.extend(layouts["skills"].render_skill(
                state.skills[skill_name],
                center_pos.offset(0, 0, -40),
            ))

    elif event_type == "agent_spawn":
        agent_id = payload.get("agent_id", "unknown")
        agent_type = payload.get("agent_type", "general")
        description = payload.get("description", "")
        state.handle_agent_spawn(agent_id, agent_type, description)

        # 更新 Hub
        commands.extend(layouts["hub"].render_update(state, center_pos))

    elif event_type == "todo_update":
        todos = payload.get("todos", [])
        state.handle_todo_update(todos)

        # 更新 Timeline
        commands.extend(layouts["timeline"].render_tasks(state.todos, center_pos.offset(0, 0, 30)))
        # 更新 Hub
        commands.extend(layouts["hub"].render_update(state, center_pos))

    elif event_type == "error":
        error_type = payload.get("error_type", "unknown")
        message = payload.get("message", "")
        state.handle_error(error_type, message)

        # 显示警告
        commands.extend(layouts["hub"].render_alert(
            f"Error: {error_type}",
            alert_type="error",
            center=center_pos,
        ))

    else:
        return [
            TextContent(
                type="text",
                text=json.dumps({"success": False, "error": f"Unknown event type: {event_type}"}),
            )
        ]

    # 执行命令
    if commands:
        await execute_commands(client_bridge, commands)

    return [
        TextContent(
            type="text",
            text=json.dumps({
                "success": True,
                "event_processed": event_type,
                "commands_executed": len(commands),
            }, indent=2),
        )
    ]

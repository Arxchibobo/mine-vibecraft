"""
Visualizer State Manager

维护 Claude Code 可视化的完整状态：
- Skills 状态和使用记录
- MCP Servers 连接状态
- Plugins 配置
- Agent 任务进度
- 会话统计
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class SkillStatus(Enum):
    """Skill 状态"""
    AVAILABLE = "available"      # 可用
    ACTIVE = "active"            # 正在执行
    RECENT = "recent"            # 最近使用 (10分钟内)
    UNAVAILABLE = "unavailable"  # 未安装/不可用


class MCPServerStatus(Enum):
    """MCP Server 连接状态"""
    ONLINE = "online"
    OFFLINE = "offline"
    RECONNECTING = "reconnecting"


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class SkillState:
    """单个 Skill 的状态"""
    name: str
    category: str
    status: SkillStatus = SkillStatus.AVAILABLE
    last_used: float | None = None
    use_count: int = 0
    description: str = ""


@dataclass
class MCPToolState:
    """单个 MCP Tool 的状态"""
    name: str
    server: str
    call_count: int = 0
    last_called: float | None = None
    is_active: bool = False


@dataclass
class MCPServerState:
    """单个 MCP Server 的状态"""
    name: str
    status: MCPServerStatus = MCPServerStatus.OFFLINE
    tools: list[MCPToolState] = field(default_factory=list)
    last_ping: float | None = None


@dataclass
class PluginState:
    """单个 Plugin 的状态"""
    name: str
    category: str
    agents: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    commands: list[str] = field(default_factory=list)
    is_active: bool = False


@dataclass
class AgentTask:
    """Agent 任务"""
    id: str
    content: str
    active_form: str
    status: TaskStatus = TaskStatus.PENDING
    created_at: float = field(default_factory=time.time)
    completed_at: float | None = None


@dataclass
class AgentState:
    """Agent 状态"""
    id: str
    agent_type: str
    description: str
    status: str = "running"
    created_at: float = field(default_factory=time.time)
    tasks: list[AgentTask] = field(default_factory=list)


@dataclass
class SessionStats:
    """会话统计"""
    start_time: float = field(default_factory=time.time)
    tool_calls: int = 0
    agent_spawns: int = 0
    tasks_completed: int = 0
    tasks_failed: int = 0
    errors: int = 0


class VisualizerState:
    """
    Visualizer 状态管理器

    维护所有可视化元素的状态，支持：
    - 状态更新
    - 事件处理
    - 持久化
    - 差量计算
    """

    def __init__(self, data_dir: Path | None = None):
        self.data_dir = data_dir or Path(__file__).parent / "data"

        # 核心状态
        self.skills: dict[str, SkillState] = {}
        self.mcp_servers: dict[str, MCPServerState] = {}
        self.plugins: dict[str, PluginState] = {}
        self.agents: dict[str, AgentState] = {}
        self.todos: list[AgentTask] = []
        self.session = SessionStats()

        # 可视化配置
        self.center: tuple[int, int, int] = (0, 64, 0)
        self.layout_mode: str = "full"  # full, compact, minimal

        # 变更追踪
        self._dirty_skills: set[str] = set()
        self._dirty_mcp: set[str] = set()
        self._dirty_plugins: set[str] = set()
        self._dirty_timeline: bool = False
        self._dirty_hub: bool = False

        # 加载初始数据
        self._load_catalogs()

    def _load_catalogs(self) -> None:
        """加载 Skills/MCP/Plugins 目录数据"""
        # 加载 Skills 目录
        skills_file = self.data_dir / "skills_catalog.json"
        if skills_file.exists():
            with open(skills_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for skill_data in data.get("skills", []):
                    skill = SkillState(
                        name=skill_data["name"],
                        category=skill_data.get("category", "general"),
                        description=skill_data.get("description", ""),
                    )
                    self.skills[skill.name] = skill

        # 加载 MCP 目录
        mcp_file = self.data_dir / "mcp_registry.json"
        if mcp_file.exists():
            with open(mcp_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for server_data in data.get("servers", []):
                    tools = [
                        MCPToolState(name=t["name"], server=server_data["name"])
                        for t in server_data.get("tools", [])
                    ]
                    server = MCPServerState(
                        name=server_data["name"],
                        tools=tools,
                    )
                    self.mcp_servers[server.name] = server

        # 加载 Plugins 目录
        plugins_file = self.data_dir / "plugins_manifest.json"
        if plugins_file.exists():
            with open(plugins_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for plugin_data in data.get("plugins", []):
                    plugin = PluginState(
                        name=plugin_data["name"],
                        category=plugin_data.get("category", "general"),
                        agents=plugin_data.get("agents", []),
                        skills=plugin_data.get("skills", []),
                        commands=plugin_data.get("commands", []),
                    )
                    self.plugins[plugin.name] = plugin

    # ===== 事件处理 =====

    def handle_tool_call(self, tool_name: str, server: str | None = None) -> None:
        """处理工具调用事件"""
        self.session.tool_calls += 1
        self._dirty_hub = True

        # 更新 MCP Tool 状态
        if server and server in self.mcp_servers:
            for tool in self.mcp_servers[server].tools:
                if tool.name == tool_name:
                    tool.call_count += 1
                    tool.last_called = time.time()
                    tool.is_active = True
                    self._dirty_mcp.add(server)
                    break

    def handle_skill_invoke(self, skill_name: str) -> None:
        """处理 Skill 调用事件"""
        if skill_name in self.skills:
            skill = self.skills[skill_name]
            skill.status = SkillStatus.ACTIVE
            skill.last_used = time.time()
            skill.use_count += 1
            self._dirty_skills.add(skill_name)

    def handle_skill_complete(self, skill_name: str) -> None:
        """处理 Skill 完成事件"""
        if skill_name in self.skills:
            skill = self.skills[skill_name]
            skill.status = SkillStatus.RECENT
            self._dirty_skills.add(skill_name)

    def handle_agent_spawn(self, agent_id: str, agent_type: str, description: str) -> None:
        """处理 Agent 创建事件"""
        self.session.agent_spawns += 1
        agent = AgentState(
            id=agent_id,
            agent_type=agent_type,
            description=description,
        )
        self.agents[agent_id] = agent
        self._dirty_hub = True

    def handle_agent_complete(self, agent_id: str) -> None:
        """处理 Agent 完成事件"""
        if agent_id in self.agents:
            self.agents[agent_id].status = "completed"
            self._dirty_hub = True

    def handle_todo_update(self, todos: list[dict[str, Any]]) -> None:
        """处理 Todo 更新事件"""
        self.todos = []
        for todo_data in todos:
            task = AgentTask(
                id=str(len(self.todos)),
                content=todo_data.get("content", ""),
                active_form=todo_data.get("activeForm", ""),
                status=TaskStatus(todo_data.get("status", "pending")),
            )
            if task.status == TaskStatus.COMPLETED:
                task.completed_at = time.time()
                self.session.tasks_completed += 1
            self.todos.append(task)
        self._dirty_timeline = True
        self._dirty_hub = True

    def handle_error(self, error_type: str, message: str) -> None:
        """处理错误事件"""
        self.session.errors += 1
        self._dirty_hub = True

    def handle_mcp_status(self, server_name: str, status: str) -> None:
        """处理 MCP Server 状态变化"""
        if server_name in self.mcp_servers:
            self.mcp_servers[server_name].status = MCPServerStatus(status)
            self.mcp_servers[server_name].last_ping = time.time()
            self._dirty_mcp.add(server_name)

    # ===== 状态查询 =====

    def get_active_skills(self) -> list[SkillState]:
        """获取活跃的 Skills"""
        return [s for s in self.skills.values() if s.status == SkillStatus.ACTIVE]

    def get_recent_skills(self, minutes: int = 10) -> list[SkillState]:
        """获取最近使用的 Skills"""
        cutoff = time.time() - minutes * 60
        return [
            s for s in self.skills.values()
            if s.last_used and s.last_used > cutoff
        ]

    def get_online_mcp_servers(self) -> list[MCPServerState]:
        """获取在线的 MCP Servers"""
        return [s for s in self.mcp_servers.values() if s.status == MCPServerStatus.ONLINE]

    def get_active_agents(self) -> list[AgentState]:
        """获取活跃的 Agents"""
        return [a for a in self.agents.values() if a.status == "running"]

    def get_session_duration(self) -> float:
        """获取会话时长（秒）"""
        return time.time() - self.session.start_time

    def get_session_duration_formatted(self) -> str:
        """获取格式化的会话时长"""
        duration = int(self.get_session_duration())
        hours, remainder = divmod(duration, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    # ===== 差量计算 =====

    def get_dirty_modules(self) -> dict[str, Any]:
        """获取需要更新的模块"""
        dirty = {}

        if self._dirty_skills:
            dirty["skills"] = [self.skills[name] for name in self._dirty_skills]

        if self._dirty_mcp:
            dirty["mcp"] = [self.mcp_servers[name] for name in self._dirty_mcp]

        if self._dirty_plugins:
            dirty["plugins"] = [self.plugins[name] for name in self._dirty_plugins]

        if self._dirty_timeline:
            dirty["timeline"] = self.todos

        if self._dirty_hub:
            dirty["hub"] = self.session

        return dirty

    def clear_dirty_flags(self) -> None:
        """清除脏标记"""
        self._dirty_skills.clear()
        self._dirty_mcp.clear()
        self._dirty_plugins.clear()
        self._dirty_timeline = False
        self._dirty_hub = False

    # ===== 持久化 =====

    def save_state(self, filepath: Path) -> None:
        """保存状态到文件"""
        state_data = {
            "timestamp": time.time(),
            "center": self.center,
            "layout_mode": self.layout_mode,
            "session": {
                "start_time": self.session.start_time,
                "tool_calls": self.session.tool_calls,
                "agent_spawns": self.session.agent_spawns,
                "tasks_completed": self.session.tasks_completed,
                "errors": self.session.errors,
            },
            "skills_usage": {
                name: {"use_count": s.use_count, "last_used": s.last_used}
                for name, s in self.skills.items()
                if s.use_count > 0
            },
            "todos": [
                {
                    "content": t.content,
                    "status": t.status.value,
                }
                for t in self.todos
            ],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(state_data, f, indent=2)

    def load_state(self, filepath: Path) -> None:
        """从文件加载状态"""
        if not filepath.exists():
            return

        with open(filepath, "r", encoding="utf-8") as f:
            state_data = json.load(f)

        self.center = tuple(state_data.get("center", [0, 64, 0]))
        self.layout_mode = state_data.get("layout_mode", "full")

        # 恢复会话统计
        session_data = state_data.get("session", {})
        self.session.start_time = session_data.get("start_time", time.time())
        self.session.tool_calls = session_data.get("tool_calls", 0)
        self.session.agent_spawns = session_data.get("agent_spawns", 0)
        self.session.tasks_completed = session_data.get("tasks_completed", 0)
        self.session.errors = session_data.get("errors", 0)

        # 恢复 Skills 使用记录
        for name, usage in state_data.get("skills_usage", {}).items():
            if name in self.skills:
                self.skills[name].use_count = usage.get("use_count", 0)
                self.skills[name].last_used = usage.get("last_used")

    # ===== 工具方法 =====

    def reset_session(self) -> None:
        """重置会话"""
        self.session = SessionStats()
        self.agents.clear()
        self.todos.clear()

        # 重置 Skills 状态
        for skill in self.skills.values():
            skill.status = SkillStatus.AVAILABLE

        # 标记全部需要更新
        self._dirty_skills = set(self.skills.keys())
        self._dirty_mcp = set(self.mcp_servers.keys())
        self._dirty_timeline = True
        self._dirty_hub = True

    def update_skill_statuses(self) -> None:
        """更新 Skills 状态（根据时间）"""
        cutoff = time.time() - 600  # 10分钟

        for skill in self.skills.values():
            if skill.status == SkillStatus.RECENT:
                if skill.last_used and skill.last_used < cutoff:
                    skill.status = SkillStatus.AVAILABLE
                    self._dirty_skills.add(skill.name)

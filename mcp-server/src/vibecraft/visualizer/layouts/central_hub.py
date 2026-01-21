"""
Central Hub Layout

圆形控制台，显示实时系统状态

布局:
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

显示内容:
  1. Token 使用量 (进度条)
  2. 活跃 Agent 数量
  3. 会话时长
  4. 最近工具调用
  5. 错误/警告计数
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..renderer import BlockType, MinecraftRenderer, Position

if TYPE_CHECKING:
    from ..state import SessionStats, VisualizerState


@dataclass
class CentralHubConfig:
    """Central Hub 配置"""
    radius: int = 8             # 半径
    height: int = 3             # 高度
    show_progress_bar: bool = True
    show_counters: bool = True
    max_token_usage: int = 100000  # 最大 token


class CentralHubLayout:
    """
    Central Hub 布局生成器

    生成圆形控制台展示系统状态
    """

    def __init__(
        self,
        renderer: MinecraftRenderer,
        config: CentralHubConfig | None = None,
    ):
        self.renderer = renderer
        self.config = config or CentralHubConfig()

    def get_hub_bounds(self, center: Position) -> tuple[Position, Position]:
        """获取 Hub 边界"""
        r = self.config.radius + 2

        min_pos = Position(center.x - r, center.y, center.z - r)
        max_pos = Position(center.x + r, center.y + self.config.height + 5, center.z + r)
        return min_pos, max_pos

    def render_full(
        self,
        state: "VisualizerState",
        center: Position,
    ) -> list[str]:
        """渲染完整的 Central Hub"""
        self.renderer.clear_commands()

        # 清空区域
        min_pos, max_pos = self.get_hub_bounds(center)
        self.renderer.clear_area(min_pos, max_pos)

        # 渲染基座
        self._render_base(center)

        # 渲染边框
        self._render_border(center)

        # 渲染显示面板
        self._render_displays(state, center)

        return self.renderer.get_commands()

    def render_update(
        self,
        state: "VisualizerState",
        center: Position,
    ) -> list[str]:
        """更新显示内容 (增量更新)"""
        self.renderer.clear_commands()

        # 只更新显示内容，不重建结构
        self._render_displays(state, center)

        return self.renderer.get_commands()

    def _render_base(self, center: Position) -> None:
        """渲染基座"""
        r = self.config.radius

        # 圆形地板
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                dist_sq = dx * dx + dz * dz
                if dist_sq <= r * r:
                    # 同心圆图案
                    if dist_sq <= (r // 3) ** 2:
                        block = "cyan_concrete"
                    elif dist_sq <= (r * 2 // 3) ** 2:
                        block = "light_blue_concrete"
                    else:
                        block = "black_concrete"

                    self.renderer.set_block(
                        center.offset(dx, -1, dz),
                        block,
                        priority=5,
                    )

    def _render_border(self, center: Position) -> None:
        """渲染边框"""
        r = self.config.radius
        h = self.config.height

        # 圆形边框
        for angle in range(0, 360, 10):
            rad = math.radians(angle)
            x = int(r * math.cos(rad))
            z = int(r * math.sin(rad))

            for dy in range(h):
                self.renderer.set_block(
                    center.offset(x, dy, z),
                    "cyan_terracotta",
                    priority=5,
                )

        # 角落柱子
        for angle in [45, 135, 225, 315]:
            rad = math.radians(angle)
            x = int(r * math.cos(rad))
            z = int(r * math.sin(rad))

            for dy in range(h + 2):
                self.renderer.set_block(
                    center.offset(x, dy, z),
                    "sea_lantern",
                    priority=5,
                )

    def _render_displays(
        self,
        state: "VisualizerState",
        center: Position,
    ) -> None:
        """渲染显示面板"""
        session = state.session

        # 中心标题
        self.renderer.summon_armor_stand(
            center.offset(dy=4),
            "§6§l═══ CLAUDE CODE ═══",
        )

        # 会话时长
        duration = state.get_session_duration_formatted()
        self.renderer.summon_armor_stand(
            center.offset(dy=3),
            f"§eSession: §f{duration}",
        )

        # 活跃 Agents
        active_agents = len(state.get_active_agents())
        self.renderer.summon_armor_stand(
            center.offset(dy=2.5),
            f"§bActive Agents: §f{active_agents}",
        )

        # 工具调用计数
        self.renderer.summon_armor_stand(
            center.offset(dy=2),
            f"§aTool Calls: §f{session.tool_calls}",
        )

        # 任务完成/失败
        self.renderer.summon_armor_stand(
            center.offset(dy=1.5),
            f"§2Completed: §f{session.tasks_completed} §c| Failed: §f{session.tasks_failed}",
        )

        # 错误计数
        if session.errors > 0:
            self.renderer.summon_armor_stand(
                center.offset(dy=1),
                f"§cErrors: §f{session.errors}",
            )

        # 进度条显示
        if self.config.show_progress_bar:
            self._render_progress_display(center)

        # 四周显示板
        self._render_side_displays(state, center)

    def _render_progress_display(self, center: Position) -> None:
        """渲染进度条显示区"""
        r = self.config.radius - 2

        # 北侧: Token 使用进度条
        progress_center = center.offset(0, 0, -r + 1)

        # 进度条背景
        self.renderer.fill(
            progress_center.offset(-5, 0, 0),
            progress_center.offset(5, 0, 0),
            "white_concrete",
        )

        # 标签
        self.renderer.summon_armor_stand(
            progress_center.offset(0, 1.5, 0),
            "§7Token Usage",
        )

    def _render_side_displays(
        self,
        state: "VisualizerState",
        center: Position,
    ) -> None:
        """渲染四周显示板"""
        r = self.config.radius - 2

        # 东侧: 最近 Skills
        recent_skills = state.get_recent_skills(minutes=10)[:3]
        if recent_skills:
            east_pos = center.offset(r - 1, 1, 0)
            self.renderer.summon_armor_stand(
                east_pos.offset(dy=2),
                "§d§lRecent Skills",
            )
            for i, skill in enumerate(recent_skills):
                self.renderer.summon_armor_stand(
                    east_pos.offset(dy=1.5 - i * 0.4),
                    f"§7• {skill.name[:15]}",
                )

        # 西侧: MCP Servers 状态
        online_servers = state.get_online_mcp_servers()[:3]
        west_pos = center.offset(-r + 1, 1, 0)
        self.renderer.summon_armor_stand(
            west_pos.offset(dy=2),
            "§a§lMCP Servers",
        )
        for i, server in enumerate(online_servers):
            self.renderer.summon_armor_stand(
                west_pos.offset(dy=1.5 - i * 0.4),
                f"§a● §7{server.name[:12]}",
            )

        # 南侧: 当前任务
        if state.todos:
            south_pos = center.offset(0, 1, r - 1)
            current_task = next(
                (t for t in state.todos if t.status.value == "in_progress"),
                None,
            )
            self.renderer.summon_armor_stand(
                south_pos.offset(dy=2),
                "§e§lCurrent Task",
            )
            if current_task:
                task_name = current_task.active_form[:20]
                self.renderer.summon_armor_stand(
                    south_pos.offset(dy=1.5),
                    f"§f{task_name}",
                )

            # 任务进度
            total = len(state.todos)
            completed = len([t for t in state.todos if t.status.value == "completed"])
            self.renderer.summon_armor_stand(
                south_pos.offset(dy=1),
                f"§7Progress: {completed}/{total}",
            )

    def render_alert(
        self,
        message: str,
        alert_type: str = "info",  # info, warning, error
        center: Position | None = None,
    ) -> list[str]:
        """渲染警告/提示"""
        self.renderer.clear_commands()

        if center is None:
            return []

        # 颜色映射
        colors = {
            "info": "§b",
            "warning": "§e",
            "error": "§c",
        }
        color = colors.get(alert_type, "§f")

        # 闪烁效果的标签
        self.renderer.summon_armor_stand(
            center.offset(dy=5),
            f"{color}§l{message}",
        )

        # 粒子效果
        particle_types = {
            "info": "minecraft:happy_villager",
            "warning": "minecraft:enchant",
            "error": "minecraft:angry_villager",
        }
        particle = particle_types.get(alert_type, "minecraft:end_rod")
        self.renderer.particle(center.offset(dy=5), particle, count=30, spread=2)

        return self.renderer.get_commands()

    def render_celebration(self, center: Position) -> list[str]:
        """渲染庆祝效果 (任务完成)"""
        self.renderer.clear_commands()

        # 烟花效果
        for i in range(3):
            self.renderer.particle(
                "minecraft:firework",
                center.offset(dy=3 + i),
                count=50,
                spread=2,
            )

        self.renderer.summon_armor_stand(
            center.offset(dy=6),
            "§a§l✓ Task Completed!",
        )

        return self.renderer.get_commands()

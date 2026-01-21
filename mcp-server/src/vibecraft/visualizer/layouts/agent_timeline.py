"""
Agent Timeline Layout

铁轨时间线，矿车代表任务，实时移动

布局:
START ═══╦═══╦═══╦═══╦═══╦═══╦═══╦═══╦═══ END
         ║   ║   ║   ║   ║   ║   ║   ║
        [T1][T2][T3][▶ ][..][..][..][..]
         ✓   ✓   ⏳

元素:
  - 已完成任务: emerald_block + ✓
  - 当前任务: minecart 移动中
  - 待执行: iron_block
  - 失败: redstone_block

实时更新:
  - TodoWrite 事件 → 更新时间线方块
  - 任务完成 → 矿车前进
  - 新增任务 → 延长轨道
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..renderer import BlockType, MinecraftRenderer, Position

if TYPE_CHECKING:
    from ..state import AgentTask, TaskStatus, VisualizerState


@dataclass
class AgentTimelineConfig:
    """Agent Timeline 配置"""
    track_length: int = 50      # 轨道长度
    task_spacing: int = 3       # 任务间距
    track_height: int = 1       # 轨道高度
    show_labels: bool = True
    animate_minecart: bool = True


class AgentTimelineLayout:
    """
    Agent Timeline 布局生成器

    生成铁轨时间线展示任务进度
    """

    def __init__(
        self,
        renderer: MinecraftRenderer,
        config: AgentTimelineConfig | None = None,
    ):
        self.renderer = renderer
        self.config = config or AgentTimelineConfig()
        self._task_positions: dict[str, Position] = {}
        self._minecart_position: Position | None = None

    def get_timeline_bounds(self, center: Position) -> tuple[Position, Position]:
        """获取时间线边界"""
        half_length = self.config.track_length // 2

        min_pos = Position(center.x - half_length - 5, center.y - 1, center.z - 3)
        max_pos = Position(center.x + half_length + 5, center.y + 5, center.z + 3)
        return min_pos, max_pos

    def render_full(
        self,
        state: "VisualizerState",
        center: Position,
    ) -> list[str]:
        """渲染完整的 Agent Timeline"""
        self.renderer.clear_commands()

        # 清空区域
        min_pos, max_pos = self.get_timeline_bounds(center)
        self.renderer.clear_area(min_pos, max_pos)

        # 渲染基座
        self._render_base(center)

        # 渲染轨道
        self._render_track(center)

        # 渲染起点和终点
        self._render_endpoints(center)

        # 渲染任务
        self._render_tasks(state.todos, center)

        # 渲染矿车 (当前任务位置)
        self._render_minecart(state.todos, center)

        return self.renderer.get_commands()

    def render_tasks(
        self,
        tasks: list["AgentTask"],
        center: Position,
    ) -> list[str]:
        """渲染任务列表 (增量更新)"""
        self.renderer.clear_commands()

        self._render_tasks(tasks, center)
        self._render_minecart(tasks, center)

        return self.renderer.get_commands()

    def render_task_update(
        self,
        task: "AgentTask",
    ) -> list[str]:
        """更新单个任务状态"""
        self.renderer.clear_commands()

        if task.id in self._task_positions:
            pos = self._task_positions[task.id]
            block = self.renderer.task_status_to_block(task.status)
            self.renderer.set_block(pos, block)

            # 完成效果
            if task.status.value == "completed":
                self.renderer.particle(
                    "minecraft:happy_villager",
                    pos.offset(dy=1),
                    count=20,
                )

        return self.renderer.get_commands()

    def _render_base(self, center: Position) -> None:
        """渲染基座"""
        half_length = self.config.track_length // 2

        # 地面
        self.renderer.fill(
            center.offset(-half_length - 2, -1, -2),
            center.offset(half_length + 2, -1, 2),
            "black_concrete",
            priority=5,
        )

    def _render_track(self, center: Position) -> None:
        """渲染轨道"""
        half_length = self.config.track_length // 2

        # 主轨道
        for x in range(-half_length, half_length + 1):
            # 轨道基座
            self.renderer.set_block(
                center.offset(x, 0, 0),
                "smooth_stone",
            )

            # 动力铁轨
            if x % 8 == 0:
                self.renderer.set_block(
                    center.offset(x, 1, 0),
                    "powered_rail",
                    state="powered=true,shape=east_west",
                )
                # 红石火把供电
                self.renderer.set_block(
                    center.offset(x, 0, 1),
                    "redstone_torch",
                )
            else:
                self.renderer.set_block(
                    center.offset(x, 1, 0),
                    "rail",
                    state="shape=east_west",
                )

    def _render_endpoints(self, center: Position) -> None:
        """渲染起点和终点"""
        half_length = self.config.track_length // 2

        # 起点
        start_pos = center.offset(-half_length - 2, 0, 0)
        self.renderer.fill(
            start_pos.offset(-1, 0, -1),
            start_pos.offset(1, 2, 1),
            "lime_concrete",
        )
        self.renderer.summon_armor_stand(
            start_pos.offset(0, 3, 0),
            "§a§lSTART",
        )

        # 终点
        end_pos = center.offset(half_length + 2, 0, 0)
        self.renderer.fill(
            end_pos.offset(-1, 0, -1),
            end_pos.offset(1, 2, 1),
            "red_concrete",
        )
        self.renderer.summon_armor_stand(
            end_pos.offset(0, 3, 0),
            "§c§lEND",
        )

    def _render_tasks(
        self,
        tasks: list["AgentTask"],
        center: Position,
    ) -> None:
        """渲染任务方块"""
        if not tasks:
            return

        half_length = self.config.track_length // 2
        spacing = self.config.task_spacing

        # 计算起始位置
        total_width = len(tasks) * spacing
        start_x = -min(total_width // 2, half_length - 5)

        for i, task in enumerate(tasks):
            x = start_x + i * spacing
            if abs(x) > half_length:
                continue

            pos = center.offset(x, 2, 0)
            self._task_positions[task.id] = pos

            # 任务方块
            block = self.renderer.task_status_to_block(task.status)
            self.renderer.set_block(pos, block)

            # 连接柱
            self.renderer.set_block(
                pos.offset(0, -1, 0),
                "iron_bars",
            )

            # 标签
            if self.config.show_labels:
                # 状态图标
                status_icon = {
                    "pending": "§7○",
                    "in_progress": "§e▶",
                    "completed": "§a✓",
                    "failed": "§c✗",
                }.get(task.status.value, "§7?")

                self.renderer.summon_armor_stand(
                    pos.offset(0, 1.5, 0),
                    status_icon,
                )

                # 任务名称 (缩短)
                name = task.active_form[:15] if task.active_form else task.content[:15]
                self.renderer.summon_armor_stand(
                    pos.offset(0, 1, 0),
                    f"§7{name}",
                )

    def _render_minecart(
        self,
        tasks: list["AgentTask"],
        center: Position,
    ) -> None:
        """渲染矿车 (当前任务位置)"""
        if not self.config.animate_minecart:
            return

        # 找到当前任务
        current_task = next(
            (t for t in tasks if t.status.value == "in_progress"),
            None,
        )

        if current_task and current_task.id in self._task_positions:
            pos = self._task_positions[current_task.id]
            minecart_pos = pos.offset(0, -1, 0)

            # 清除旧矿车
            if self._minecart_position:
                self.renderer.kill_entities(
                    "minecart",
                    self._minecart_position,
                    radius=5,
                )

            # 召唤新矿车
            self.renderer.summon_minecart(minecart_pos, "gold_block")
            self._minecart_position = minecart_pos

    def render_task_complete_animation(
        self,
        task_id: str,
    ) -> list[str]:
        """渲染任务完成动画"""
        self.renderer.clear_commands()

        if task_id in self._task_positions:
            pos = self._task_positions[task_id]

            # 庆祝粒子
            self.renderer.particle(
                "minecraft:totem_of_undying",
                pos.offset(dy=1),
                count=30,
                spread=0.5,
            )

            # 更新方块为绿色
            self.renderer.set_block(pos, BlockType.TASK_COMPLETED)

        return self.renderer.get_commands()

    def render_progress_bar(
        self,
        tasks: list["AgentTask"],
        center: Position,
    ) -> list[str]:
        """渲染简化的进度条"""
        self.renderer.clear_commands()

        if not tasks:
            return []

        total = len(tasks)
        completed = len([t for t in tasks if t.status.value == "completed"])
        progress = completed / total if total > 0 else 0

        # 进度条位置 (在轨道下方)
        bar_center = center.offset(0, -2, 2)
        bar_length = min(20, self.config.track_length // 2)

        self.renderer.render_progress_bar(
            bar_center.offset(-bar_length // 2, 0, 0),
            progress,
            length=bar_length,
            direction="x",
            filled_block=BlockType.TASK_COMPLETED,
            empty_block=BlockType.TASK_PENDING,
        )

        # 进度文本
        self.renderer.summon_armor_stand(
            bar_center.offset(0, 1, 0),
            f"§7Progress: §f{completed}/{total} ({int(progress * 100)}%)",
        )

        return self.renderer.get_commands()

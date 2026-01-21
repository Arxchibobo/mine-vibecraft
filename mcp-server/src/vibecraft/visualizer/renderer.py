"""
Minecraft Renderer

生成 Minecraft 命令来渲染可视化元素：
- 方块放置/替换
- Armor Stand 全息文字
- 粒子效果
- 实体操作
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .state import (
        AgentTask,
        MCPServerState,
        PluginState,
        SessionStats,
        SkillState,
        SkillStatus,
        TaskStatus,
    )


class BlockType(Enum):
    """可视化用的方块类型"""
    # Skills Matrix
    SKILL_AVAILABLE = "sea_lantern"
    SKILL_ACTIVE = "glowstone"
    SKILL_RECENT = "diamond_block"
    SKILL_UNAVAILABLE = "gray_concrete"

    # MCP Tower
    MCP_ONLINE = "emerald_block"
    MCP_OFFLINE = "redstone_block"
    MCP_RECONNECTING = "gold_block"
    MCP_TOOL = "smooth_quartz"
    MCP_TOOL_ACTIVE = "prismarine"

    # Timeline
    TASK_PENDING = "iron_block"
    TASK_IN_PROGRESS = "gold_block"
    TASK_COMPLETED = "emerald_block"
    TASK_FAILED = "redstone_block"
    RAIL = "powered_rail"
    RAIL_DETECTOR = "detector_rail"

    # Central Hub
    HUB_BASE = "black_concrete"
    HUB_BORDER = "cyan_terracotta"
    HUB_DISPLAY = "white_concrete"
    HUB_INDICATOR = "lime_concrete"

    # Plugins Garden
    TREE_TRUNK = "oak_log"
    TREE_LEAVES_DEV = "oak_leaves"
    TREE_LEAVES_SECURITY = "spruce_leaves"
    TREE_LEAVES_DOCS = "birch_leaves"
    TREE_LEAVES_INFRA = "jungle_leaves"
    TREE_LEAVES_AI = "azalea_leaves"

    # General
    AIR = "air"
    GLASS = "glass"
    BARRIER = "barrier"


@dataclass
class Position:
    """3D 坐标"""
    x: int
    y: int
    z: int

    def offset(self, dx: int = 0, dy: int = 0, dz: int = 0) -> "Position":
        return Position(self.x + dx, self.y + dy, self.z + dz)

    def to_tuple(self) -> tuple[int, int, int]:
        return (self.x, self.y, self.z)

    def __str__(self) -> str:
        return f"{self.x} {self.y} {self.z}"


@dataclass
class RenderCommand:
    """渲染命令"""
    command: str
    priority: int = 0  # 高优先级先执行
    delay_ms: int = 0  # 延迟执行


class MinecraftRenderer:
    """
    Minecraft 命令渲染器

    将可视化状态转换为 Minecraft 命令
    """

    def __init__(self, center: tuple[int, int, int] = (0, 64, 0)):
        self.center = Position(*center)
        self._commands: list[RenderCommand] = []

    def set_center(self, x: int, y: int, z: int) -> None:
        """设置渲染中心"""
        self.center = Position(x, y, z)

    def clear_commands(self) -> None:
        """清空命令队列"""
        self._commands.clear()

    def get_commands(self) -> list[str]:
        """获取排序后的命令列表"""
        sorted_cmds = sorted(self._commands, key=lambda c: -c.priority)
        return [c.command for c in sorted_cmds]

    # ===== 基础渲染命令 =====

    def set_block(
        self,
        pos: Position,
        block: BlockType | str,
        state: str | None = None,
        priority: int = 0,
    ) -> None:
        """放置单个方块"""
        block_name = block.value if isinstance(block, BlockType) else block
        if state:
            block_name = f"{block_name}[{state}]"
        cmd = f"/setblock {pos} {block_name}"
        self._commands.append(RenderCommand(cmd, priority))

    def fill(
        self,
        pos1: Position,
        pos2: Position,
        block: BlockType | str,
        state: str | None = None,
        mode: str = "replace",
        priority: int = 0,
    ) -> None:
        """填充区域"""
        block_name = block.value if isinstance(block, BlockType) else block
        if state:
            block_name = f"{block_name}[{state}]"
        cmd = f"/fill {pos1} {pos2} {block_name} {mode}"
        self._commands.append(RenderCommand(cmd, priority))

    def clone(
        self,
        src1: Position,
        src2: Position,
        dest: Position,
        mode: str = "replace",
        priority: int = 0,
    ) -> None:
        """复制区域"""
        cmd = f"/clone {src1} {src2} {dest} {mode}"
        self._commands.append(RenderCommand(cmd, priority))

    def summon_armor_stand(
        self,
        pos: Position,
        name: str,
        invisible: bool = True,
        marker: bool = True,
        custom_name_visible: bool = True,
        priority: int = 0,
    ) -> None:
        """召唤 Armor Stand 全息文字"""
        nbt_parts = [
            f'CustomName:\'{{"text":"{name}"}}\'',
            f"CustomNameVisible:{1 if custom_name_visible else 0}b",
            f"Invisible:{1 if invisible else 0}b",
            f"Marker:{1 if marker else 0}b",
            "NoGravity:1b",
        ]
        nbt = "{" + ",".join(nbt_parts) + "}"
        cmd = f"/summon armor_stand {pos.x} {pos.y} {pos.z} {nbt}"
        self._commands.append(RenderCommand(cmd, priority))

    def kill_entities(
        self,
        entity_type: str,
        pos: Position,
        radius: int,
        priority: int = 0,
    ) -> None:
        """删除区域内的实体"""
        cmd = f"/kill @e[type={entity_type},x={pos.x},y={pos.y},z={pos.z},distance=..{radius}]"
        self._commands.append(RenderCommand(cmd, priority))

    def particle(
        self,
        particle_type: str,
        pos: Position,
        count: int = 10,
        spread: float = 0.5,
        speed: float = 0.1,
        priority: int = 0,
    ) -> None:
        """生成粒子效果"""
        cmd = f"/particle {particle_type} {pos.x} {pos.y} {pos.z} {spread} {spread} {spread} {speed} {count}"
        self._commands.append(RenderCommand(cmd, priority))

    def summon_minecart(
        self,
        pos: Position,
        display_block: str | None = None,
        priority: int = 0,
    ) -> None:
        """召唤矿车"""
        if display_block:
            nbt = f'{{CustomDisplayTile:1b,DisplayTile:"{display_block}",DisplayOffset:6}}'
            cmd = f"/summon minecart {pos.x} {pos.y} {pos.z} {nbt}"
        else:
            cmd = f"/summon minecart {pos.x} {pos.y} {pos.z}"
        self._commands.append(RenderCommand(cmd, priority))

    # ===== 高级渲染方法 =====

    def render_text_display(
        self,
        pos: Position,
        lines: list[str],
        line_spacing: float = 0.3,
        priority: int = 0,
    ) -> None:
        """渲染多行文字显示"""
        for i, line in enumerate(lines):
            line_pos = pos.offset(dy=int(-i * line_spacing * 10) / 10)
            self.summon_armor_stand(line_pos, line, priority=priority)

    def render_progress_bar(
        self,
        pos: Position,
        progress: float,  # 0.0 - 1.0
        length: int = 10,
        direction: str = "x",  # x, y, z
        filled_block: BlockType = BlockType.HUB_INDICATOR,
        empty_block: BlockType = BlockType.HUB_DISPLAY,
        priority: int = 0,
    ) -> None:
        """渲染进度条"""
        filled_count = int(progress * length)

        for i in range(length):
            if direction == "x":
                block_pos = pos.offset(dx=i)
            elif direction == "y":
                block_pos = pos.offset(dy=i)
            else:
                block_pos = pos.offset(dz=i)

            block = filled_block if i < filled_count else empty_block
            self.set_block(block_pos, block, priority=priority)

    def render_counter(
        self,
        pos: Position,
        value: int,
        label: str,
        priority: int = 0,
    ) -> None:
        """渲染数字计数器"""
        self.summon_armor_stand(pos, f"{label}: {value}", priority=priority)

    def clear_area(
        self,
        pos1: Position,
        pos2: Position,
        priority: int = 10,  # 高优先级
    ) -> None:
        """清空区域"""
        self.fill(pos1, pos2, BlockType.AIR, priority=priority)
        # 也清除实体
        center = Position(
            (pos1.x + pos2.x) // 2,
            (pos1.y + pos2.y) // 2,
            (pos1.z + pos2.z) // 2,
        )
        radius = max(
            abs(pos2.x - pos1.x),
            abs(pos2.y - pos1.y),
            abs(pos2.z - pos1.z),
        ) // 2 + 5
        self.kill_entities("armor_stand", center, radius, priority=priority)

    # ===== 状态到方块的映射 =====

    @staticmethod
    def skill_status_to_block(status: "SkillStatus") -> BlockType:
        """Skill 状态 -> 方块类型"""
        from .state import SkillStatus

        mapping = {
            SkillStatus.AVAILABLE: BlockType.SKILL_AVAILABLE,
            SkillStatus.ACTIVE: BlockType.SKILL_ACTIVE,
            SkillStatus.RECENT: BlockType.SKILL_RECENT,
            SkillStatus.UNAVAILABLE: BlockType.SKILL_UNAVAILABLE,
        }
        return mapping.get(status, BlockType.SKILL_UNAVAILABLE)

    @staticmethod
    def mcp_status_to_block(status: "MCPServerStatus") -> BlockType:
        """MCP Server 状态 -> 方块类型"""
        from .state import MCPServerStatus

        mapping = {
            MCPServerStatus.ONLINE: BlockType.MCP_ONLINE,
            MCPServerStatus.OFFLINE: BlockType.MCP_OFFLINE,
            MCPServerStatus.RECONNECTING: BlockType.MCP_RECONNECTING,
        }
        return mapping.get(status, BlockType.MCP_OFFLINE)

    @staticmethod
    def task_status_to_block(status: "TaskStatus") -> BlockType:
        """任务状态 -> 方块类型"""
        from .state import TaskStatus

        mapping = {
            TaskStatus.PENDING: BlockType.TASK_PENDING,
            TaskStatus.IN_PROGRESS: BlockType.TASK_IN_PROGRESS,
            TaskStatus.COMPLETED: BlockType.TASK_COMPLETED,
            TaskStatus.FAILED: BlockType.TASK_FAILED,
        }
        return mapping.get(status, BlockType.TASK_PENDING)

    @staticmethod
    def plugin_category_to_leaves(category: str) -> BlockType:
        """Plugin 类别 -> 树叶类型"""
        mapping = {
            "development": BlockType.TREE_LEAVES_DEV,
            "backend-development": BlockType.TREE_LEAVES_DEV,
            "frontend-mobile-development": BlockType.TREE_LEAVES_DEV,
            "security": BlockType.TREE_LEAVES_SECURITY,
            "security-scanning": BlockType.TREE_LEAVES_SECURITY,
            "documentation": BlockType.TREE_LEAVES_DOCS,
            "documentation-generation": BlockType.TREE_LEAVES_DOCS,
            "infrastructure": BlockType.TREE_LEAVES_INFRA,
            "cloud-infrastructure": BlockType.TREE_LEAVES_INFRA,
            "ai": BlockType.TREE_LEAVES_AI,
            "llm-application-dev": BlockType.TREE_LEAVES_AI,
            "machine-learning-ops": BlockType.TREE_LEAVES_AI,
        }
        return mapping.get(category.lower(), BlockType.TREE_LEAVES_DEV)

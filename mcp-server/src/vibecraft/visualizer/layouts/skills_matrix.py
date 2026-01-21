"""
Skills Matrix Layout

81 个 Skills 排列成 9x9 立体矩阵
每个技能用不同方块表示其状态

布局:
  Y=5  ┌───┬───┬───┬───┬───┬───┬───┬───┬───┐
       │ S │ S │ S │ S │ S │ S │ S │ S │ S │  Category: Backend
  Y=4  ├───┼───┼───┼───┼───┼───┼───┼───┼───┤
       │ S │ S │ S │ S │ S │ S │ S │ S │ S │  Category: Frontend
  Y=3  ├───┼───┼───┼───┼───┼───┼───┼───┼───┤
       │ S │ S │ S │ S │ S │ S │ S │ S │ S │  Category: DevOps
       └───┴───┴───┴───┴───┴───┴───┴───┴───┘

状态 -> 方块:
  - 可用: sea_lantern (发光)
  - 活跃: glowstone + 粒子效果
  - 最近使用: diamond_block
  - 未安装: gray_concrete
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..renderer import BlockType, MinecraftRenderer, Position

if TYPE_CHECKING:
    from ..state import SkillState, VisualizerState


@dataclass
class SkillsMatrixConfig:
    """Skills Matrix 配置"""
    grid_size: int = 9          # 9x9 网格
    block_spacing: int = 2      # 方块间距
    layer_height: int = 4       # 层间高度
    show_labels: bool = True    # 显示标签
    show_particles: bool = True # 显示粒子效果


# 技能类别 -> 层级
CATEGORY_LAYERS = {
    # 后端开发 (Layer 0-2)
    "backend": 0,
    "api": 0,
    "database": 1,
    "infrastructure": 2,

    # 前端开发 (Layer 3-4)
    "frontend": 3,
    "mobile": 4,

    # DevOps (Layer 5-6)
    "devops": 5,
    "security": 6,

    # AI/ML (Layer 7)
    "ai": 7,
    "ml": 7,

    # 其他 (Layer 8)
    "general": 8,
    "documentation": 8,
}


class SkillsMatrixLayout:
    """
    Skills Matrix 布局生成器

    生成 9x9 的技能矩阵，支持：
    - 按类别分层
    - 状态可视化
    - 交互标签
    """

    def __init__(
        self,
        renderer: MinecraftRenderer,
        config: SkillsMatrixConfig | None = None,
    ):
        self.renderer = renderer
        self.config = config or SkillsMatrixConfig()
        self._skill_positions: dict[str, Position] = {}

    def get_matrix_bounds(self, center: Position) -> tuple[Position, Position]:
        """获取矩阵边界"""
        size = self.config.grid_size * self.config.block_spacing
        layers = 9  # 最多 9 层

        min_pos = Position(
            center.x - size // 2,
            center.y,
            center.z - size // 2,
        )
        max_pos = Position(
            center.x + size // 2,
            center.y + layers * self.config.layer_height,
            center.z + size // 2,
        )
        return min_pos, max_pos

    def render_full(
        self,
        state: "VisualizerState",
        center: Position,
    ) -> list[str]:
        """渲染完整的 Skills Matrix"""
        self.renderer.clear_commands()

        # 清空区域
        min_pos, max_pos = self.get_matrix_bounds(center)
        self.renderer.clear_area(min_pos, max_pos)

        # 渲染基座
        self._render_base(center)

        # 按类别分组技能
        skills_by_category = self._group_skills_by_category(state.skills)

        # 渲染每个类别的技能
        for category, skills in skills_by_category.items():
            layer = CATEGORY_LAYERS.get(category, 8)
            self._render_category_layer(skills, center, layer)

        # 渲染类别标签
        if self.config.show_labels:
            self._render_category_labels(center)

        return self.renderer.get_commands()

    def render_skill(
        self,
        skill: "SkillState",
        center: Position,
    ) -> list[str]:
        """渲染单个 Skill (增量更新)"""
        self.renderer.clear_commands()

        if skill.name in self._skill_positions:
            pos = self._skill_positions[skill.name]
            block = self.renderer.skill_status_to_block(skill.status)
            self.renderer.set_block(pos, block)

            # 活跃状态添加粒子效果
            if self.config.show_particles and skill.status.value == "active":
                self.renderer.particle("minecraft:end_rod", pos, count=20, spread=0.3)

        return self.renderer.get_commands()

    def render_skills(
        self,
        skills: list["SkillState"],
        center: Position,
    ) -> list[str]:
        """渲染多个 Skills (批量更新)"""
        self.renderer.clear_commands()

        for skill in skills:
            if skill.name in self._skill_positions:
                pos = self._skill_positions[skill.name]
                block = self.renderer.skill_status_to_block(skill.status)
                self.renderer.set_block(pos, block)

                if self.config.show_particles and skill.status.value == "active":
                    self.renderer.particle("minecraft:end_rod", pos)

        return self.renderer.get_commands()

    def _render_base(self, center: Position) -> None:
        """渲染基座"""
        size = self.config.grid_size * self.config.block_spacing
        half = size // 2

        # 地板
        self.renderer.fill(
            center.offset(-half, -1, -half),
            center.offset(half, -1, half),
            "black_concrete",
            priority=5,
        )

        # 边框
        self.renderer.fill(
            center.offset(-half - 1, -1, -half - 1),
            center.offset(-half - 1, 0, half + 1),
            "cyan_terracotta",
            priority=5,
        )
        self.renderer.fill(
            center.offset(half + 1, -1, -half - 1),
            center.offset(half + 1, 0, half + 1),
            "cyan_terracotta",
            priority=5,
        )
        self.renderer.fill(
            center.offset(-half - 1, -1, -half - 1),
            center.offset(half + 1, 0, -half - 1),
            "cyan_terracotta",
            priority=5,
        )
        self.renderer.fill(
            center.offset(-half - 1, -1, half + 1),
            center.offset(half + 1, 0, half + 1),
            "cyan_terracotta",
            priority=5,
        )

    def _group_skills_by_category(
        self,
        skills: dict[str, "SkillState"],
    ) -> dict[str, list["SkillState"]]:
        """按类别分组技能"""
        grouped: dict[str, list["SkillState"]] = {}

        for skill in skills.values():
            category = self._normalize_category(skill.category)
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(skill)

        return grouped

    def _normalize_category(self, category: str) -> str:
        """规范化类别名称"""
        category_lower = category.lower()

        # 映射到主类别
        if "backend" in category_lower or "api" in category_lower:
            return "backend"
        elif "frontend" in category_lower or "ui" in category_lower:
            return "frontend"
        elif "mobile" in category_lower:
            return "mobile"
        elif "devops" in category_lower or "deploy" in category_lower:
            return "devops"
        elif "security" in category_lower:
            return "security"
        elif "database" in category_lower or "sql" in category_lower:
            return "database"
        elif "ai" in category_lower or "ml" in category_lower:
            return "ai"
        elif "infra" in category_lower or "cloud" in category_lower:
            return "infrastructure"
        elif "doc" in category_lower:
            return "documentation"
        else:
            return "general"

    def _render_category_layer(
        self,
        skills: list["SkillState"],
        center: Position,
        layer: int,
    ) -> None:
        """渲染一个类别层的技能"""
        spacing = self.config.block_spacing
        grid_size = self.config.grid_size
        half = (grid_size * spacing) // 2
        y = center.y + layer * self.config.layer_height

        # 将技能排列在网格中
        for i, skill in enumerate(skills[:81]):  # 最多 81 个
            row = i // grid_size
            col = i % grid_size

            x = center.x - half + col * spacing
            z = center.z - half + row * spacing
            pos = Position(x, y, z)

            # 记录位置
            self._skill_positions[skill.name] = pos

            # 放置方块
            block = self.renderer.skill_status_to_block(skill.status)
            self.renderer.set_block(pos, block)

            # 添加标签
            if self.config.show_labels:
                # 缩短名称
                short_name = skill.name[:12] if len(skill.name) > 12 else skill.name
                self.renderer.summon_armor_stand(
                    pos.offset(dy=1),
                    short_name,
                )

    def _render_category_labels(self, center: Position) -> None:
        """渲染类别标签"""
        spacing = self.config.block_spacing
        grid_size = self.config.grid_size
        half = (grid_size * spacing) // 2

        categories = [
            "Backend",
            "Database",
            "Infrastructure",
            "Frontend",
            "Mobile",
            "DevOps",
            "Security",
            "AI/ML",
            "General",
        ]

        for layer, category in enumerate(categories):
            y = center.y + layer * self.config.layer_height
            label_pos = Position(center.x - half - 3, y + 1, center.z)
            self.renderer.summon_armor_stand(label_pos, f"§e{category}")

    def highlight_skill(
        self,
        skill_name: str,
        duration_seconds: int = 5,
    ) -> list[str]:
        """高亮指定 Skill"""
        self.renderer.clear_commands()

        if skill_name in self._skill_positions:
            pos = self._skill_positions[skill_name]
            # 使用粒子效果高亮
            for _ in range(duration_seconds * 4):  # 每秒 4 次
                self.renderer.particle(
                    "minecraft:totem_of_undying",
                    pos,
                    count=30,
                    spread=0.5,
                    speed=0.3,
                )

        return self.renderer.get_commands()

    def get_skill_at_position(
        self,
        pos: Position,
        tolerance: int = 1,
    ) -> str | None:
        """根据位置获取 Skill 名称"""
        for name, skill_pos in self._skill_positions.items():
            if (
                abs(skill_pos.x - pos.x) <= tolerance
                and abs(skill_pos.y - pos.y) <= tolerance
                and abs(skill_pos.z - pos.z) <= tolerance
            ):
                return name
        return None

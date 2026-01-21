"""
Plugins Garden Layout

有机花园布局，每个 Plugin 是一棵"功能树"

布局:
    🌳 backend-development     🌲 security-scanning
         /|\                        /|\
        / | \                      / | \
       T  T  T                    T  T  T
      (tools)                   (tools)

树的表示:
  - 树干高度 = Plugin 复杂度 (agents + skills + commands)
  - 树叶颜色 = Plugin 类别
  - 果实 = 子 Agent 类型

类别颜色:
  - Development: oak_leaves (绿)
  - Security: spruce_leaves (深绿)
  - Documentation: birch_leaves (浅黄)
  - Infrastructure: jungle_leaves (茂密)
  - AI/ML: azalea_leaves (粉)
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..renderer import BlockType, MinecraftRenderer, Position

if TYPE_CHECKING:
    from ..state import PluginState, VisualizerState


@dataclass
class PluginsGardenConfig:
    """Plugins Garden 配置"""
    garden_radius: int = 30     # 花园半径
    tree_spacing: int = 8       # 树间距
    min_tree_height: int = 4    # 最小树高
    max_tree_height: int = 12   # 最大树高
    show_labels: bool = True
    show_paths: bool = True


class PluginsGardenLayout:
    """
    Plugins Garden 布局生成器

    生成有机花园布局展示 Plugins
    """

    def __init__(
        self,
        renderer: MinecraftRenderer,
        config: PluginsGardenConfig | None = None,
    ):
        self.renderer = renderer
        self.config = config or PluginsGardenConfig()
        self._plugin_positions: dict[str, Position] = {}
        self._tree_seed = random.randint(0, 10000)

    def get_garden_bounds(self, center: Position) -> tuple[Position, Position]:
        """获取花园边界"""
        r = self.config.garden_radius + 5

        min_pos = Position(center.x - r, center.y - 1, center.z - r)
        max_pos = Position(
            center.x + r,
            center.y + self.config.max_tree_height + 5,
            center.z + r,
        )
        return min_pos, max_pos

    def render_full(
        self,
        state: "VisualizerState",
        center: Position,
    ) -> list[str]:
        """渲染完整的 Plugins Garden"""
        self.renderer.clear_commands()

        plugins = list(state.plugins.values())
        if not plugins:
            return []

        # 清空区域
        min_pos, max_pos = self.get_garden_bounds(center)
        self.renderer.clear_area(min_pos, max_pos)

        # 渲染地面
        self._render_ground(center)

        # 渲染路径
        if self.config.show_paths:
            self._render_paths(center, len(plugins))

        # 计算树的位置 (螺旋布局)
        positions = self._calculate_tree_positions(center, len(plugins))

        # 渲染每棵树
        for i, plugin in enumerate(plugins):
            pos = positions[i] if i < len(positions) else center
            self._plugin_positions[plugin.name] = pos
            self._render_plugin_tree(plugin, pos)

        return self.renderer.get_commands()

    def render_plugin(
        self,
        plugin: "PluginState",
    ) -> list[str]:
        """渲染单个 Plugin (增量更新)"""
        self.renderer.clear_commands()

        if plugin.name in self._plugin_positions:
            pos = self._plugin_positions[plugin.name]
            self._render_plugin_tree(plugin, pos)

        return self.renderer.get_commands()

    def _render_ground(self, center: Position) -> None:
        """渲染地面"""
        r = self.config.garden_radius

        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                dist_sq = dx * dx + dz * dz
                if dist_sq <= r * r:
                    # 随机草地纹理
                    seed = (dx * 13 + dz * 7 + self._tree_seed) % 100
                    if seed < 60:
                        block = "grass_block"
                    elif seed < 80:
                        block = "podzol"
                    elif seed < 90:
                        block = "coarse_dirt"
                    else:
                        block = "moss_block"

                    self.renderer.set_block(
                        center.offset(dx, -1, dz),
                        block,
                        priority=5,
                    )

    def _render_paths(self, center: Position, num_plugins: int) -> None:
        """渲染路径"""
        # 从中心向外辐射的路径
        for angle in range(0, 360, 60):
            rad = math.radians(angle)
            for r in range(3, self.config.garden_radius - 5):
                x = int(r * math.cos(rad))
                z = int(r * math.sin(rad))
                self.renderer.set_block(
                    center.offset(x, -1, z),
                    "gravel",
                    priority=4,
                )

    def _calculate_tree_positions(
        self,
        center: Position,
        num_plugins: int,
    ) -> list[Position]:
        """计算树的位置 (螺旋布局)"""
        positions = []
        spacing = self.config.tree_spacing

        # 使用黄金角螺旋分布
        golden_angle = math.pi * (3 - math.sqrt(5))

        for i in range(num_plugins):
            r = spacing * math.sqrt(i + 1)
            if r > self.config.garden_radius - 5:
                r = self.config.garden_radius - 5

            angle = i * golden_angle
            x = int(r * math.cos(angle))
            z = int(r * math.sin(angle))

            positions.append(center.offset(x, 0, z))

        return positions

    def _render_plugin_tree(
        self,
        plugin: "PluginState",
        pos: Position,
    ) -> None:
        """渲染一棵 Plugin 树"""
        # 计算树高 (基于复杂度)
        complexity = len(plugin.agents) + len(plugin.skills) + len(plugin.commands)
        height = min(
            self.config.min_tree_height + complexity,
            self.config.max_tree_height,
        )

        # 获取树叶类型
        leaves = self.renderer.plugin_category_to_leaves(plugin.category)

        # 树干
        for dy in range(height):
            self.renderer.set_block(
                pos.offset(0, dy, 0),
                BlockType.TREE_TRUNK,
            )

        # 树冠 (球形)
        crown_radius = max(2, height // 3)
        crown_center = pos.offset(0, height, 0)

        for dx in range(-crown_radius, crown_radius + 1):
            for dy in range(-crown_radius // 2, crown_radius + 1):
                for dz in range(-crown_radius, crown_radius + 1):
                    dist_sq = dx * dx + dy * dy + dz * dz
                    if dist_sq <= crown_radius * crown_radius:
                        # 随机稀疏效果
                        if random.random() > 0.2:
                            self.renderer.set_block(
                                crown_center.offset(dx, dy, dz),
                                leaves,
                            )

        # 活跃状态: 发光果实
        if plugin.is_active:
            for _ in range(min(3, len(plugin.agents))):
                dx = random.randint(-crown_radius + 1, crown_radius - 1)
                dy = random.randint(0, crown_radius)
                dz = random.randint(-crown_radius + 1, crown_radius - 1)
                self.renderer.set_block(
                    crown_center.offset(dx, dy, dz),
                    "shroomlight",
                )

        # 标签
        if self.config.show_labels:
            # 名称牌
            self.renderer.summon_armor_stand(
                pos.offset(0, height + crown_radius + 1, 0),
                f"§e{plugin.name}",
            )

            # 组件数量
            self.renderer.summon_armor_stand(
                pos.offset(0, height + crown_radius + 0.5, 0),
                f"§7A:{len(plugin.agents)} S:{len(plugin.skills)} C:{len(plugin.commands)}",
            )

    def highlight_plugin(
        self,
        plugin_name: str,
    ) -> list[str]:
        """高亮指定 Plugin"""
        self.renderer.clear_commands()

        if plugin_name in self._plugin_positions:
            pos = self._plugin_positions[plugin_name]
            # 萤火虫效果
            self.renderer.particle(
                "minecraft:glow",
                pos.offset(dy=5),
                count=50,
                spread=3,
            )

        return self.renderer.get_commands()

    def get_plugin_at_position(
        self,
        pos: Position,
        tolerance: int = 3,
    ) -> str | None:
        """根据位置获取 Plugin 名称"""
        for name, plugin_pos in self._plugin_positions.items():
            if (
                abs(plugin_pos.x - pos.x) <= tolerance
                and abs(plugin_pos.z - pos.z) <= tolerance
            ):
                return name
        return None

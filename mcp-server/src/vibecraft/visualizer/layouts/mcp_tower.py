"""
MCP Tower Layout

垂直塔楼，每层代表一个 MCP Server
工具围绕塔身排列

布局:
      ┌─────┐
      │ TOP │  ← 活跃连接指示器
      ├─────┤
   ┌──┤     ├──┐
   │T1│SERVER│T2│  ← MCP Server 层
   └──┤     ├──┘
      ├─────┤
      │BASE │
      └─────┘

每层结构:
  - 中心: MCP Server 名称 (告示牌)
  - 环绕: 该 Server 的工具 (方块)
  - 颜色: 连接状态 (绿=在线, 红=离线, 黄=重连中)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..renderer import BlockType, MinecraftRenderer, Position

if TYPE_CHECKING:
    from ..state import MCPServerState, MCPToolState, VisualizerState


@dataclass
class MCPTowerConfig:
    """MCP Tower 配置"""
    tower_radius: int = 3       # 塔半径
    layer_height: int = 6       # 层高度
    tool_ring_radius: int = 5   # 工具环半径
    max_tools_per_ring: int = 16 # 每环最多工具数
    show_labels: bool = True


class MCPTowerLayout:
    """
    MCP Tower 布局生成器

    生成垂直塔楼展示 MCP Servers 和工具
    """

    def __init__(
        self,
        renderer: MinecraftRenderer,
        config: MCPTowerConfig | None = None,
    ):
        self.renderer = renderer
        self.config = config or MCPTowerConfig()
        self._server_positions: dict[str, Position] = {}
        self._tool_positions: dict[str, Position] = {}

    def get_tower_bounds(
        self,
        center: Position,
        num_servers: int,
    ) -> tuple[Position, Position]:
        """获取塔楼边界"""
        radius = self.config.tool_ring_radius + 2
        height = num_servers * self.config.layer_height + 10

        min_pos = Position(center.x - radius, center.y, center.z - radius)
        max_pos = Position(center.x + radius, center.y + height, center.z + radius)
        return min_pos, max_pos

    def render_full(
        self,
        state: "VisualizerState",
        center: Position,
    ) -> list[str]:
        """渲染完整的 MCP Tower"""
        self.renderer.clear_commands()

        servers = list(state.mcp_servers.values())
        if not servers:
            return []

        # 清空区域
        min_pos, max_pos = self.get_tower_bounds(center, len(servers))
        self.renderer.clear_area(min_pos, max_pos)

        # 渲染基座
        self._render_base(center)

        # 渲染每个 Server 层
        for i, server in enumerate(servers):
            layer_center = center.offset(dy=i * self.config.layer_height + 3)
            self._render_server_layer(server, layer_center, i)

        # 渲染塔顶
        top_y = len(servers) * self.config.layer_height + 3
        self._render_tower_top(center.offset(dy=top_y))

        return self.renderer.get_commands()

    def render_server(
        self,
        server: "MCPServerState",
        center: Position,
    ) -> list[str]:
        """渲染单个 Server (增量更新)"""
        self.renderer.clear_commands()

        if server.name in self._server_positions:
            layer_center = self._server_positions[server.name]

            # 更新中心方块颜色
            status_block = self.renderer.mcp_status_to_block(server.status)
            self._render_tower_core(layer_center, status_block, 1)

        return self.renderer.get_commands()

    def render_tool(
        self,
        tool: "MCPToolState",
        active: bool = False,
    ) -> list[str]:
        """渲染单个工具状态"""
        self.renderer.clear_commands()

        if tool.name in self._tool_positions:
            pos = self._tool_positions[tool.name]
            if active:
                self.renderer.set_block(pos, BlockType.MCP_TOOL_ACTIVE)
                self.renderer.particle("minecraft:happy_villager", pos, count=10)
            else:
                self.renderer.set_block(pos, BlockType.MCP_TOOL)

        return self.renderer.get_commands()

    def _render_base(self, center: Position) -> None:
        """渲染塔基座"""
        radius = self.config.tower_radius + 1

        # 圆形基座
        for dx in range(-radius, radius + 1):
            for dz in range(-radius, radius + 1):
                if dx * dx + dz * dz <= radius * radius:
                    self.renderer.set_block(
                        center.offset(dx, -1, dz),
                        "black_concrete",
                        priority=5,
                    )

        # 装饰边框
        for angle in range(0, 360, 30):
            rad = math.radians(angle)
            x = int(radius * math.cos(rad))
            z = int(radius * math.sin(rad))
            self.renderer.set_block(
                center.offset(x, 0, z),
                "cyan_terracotta",
                priority=5,
            )

    def _render_server_layer(
        self,
        server: "MCPServerState",
        center: Position,
        layer_index: int,
    ) -> None:
        """渲染一个 Server 层"""
        # 记录位置
        self._server_positions[server.name] = center

        # 塔芯
        status_block = self.renderer.mcp_status_to_block(server.status)
        self._render_tower_core(center, status_block, self.config.layer_height - 2)

        # 平台
        self._render_platform(center)

        # 工具环
        self._render_tool_ring(server.tools, center)

        # 服务器名称标签
        if self.config.show_labels:
            self.renderer.summon_armor_stand(
                center.offset(dy=2),
                f"§b{server.name}",
            )

            # 工具数量
            self.renderer.summon_armor_stand(
                center.offset(dy=1),
                f"§7Tools: {len(server.tools)}",
            )

    def _render_tower_core(
        self,
        center: Position,
        block: BlockType,
        height: int,
    ) -> None:
        """渲染塔芯"""
        radius = self.config.tower_radius

        for dy in range(height):
            for dx in range(-1, 2):
                for dz in range(-1, 2):
                    self.renderer.set_block(
                        center.offset(dx, dy, dz),
                        block,
                    )

    def _render_platform(self, center: Position) -> None:
        """渲染平台"""
        radius = self.config.tower_radius + 1

        for dx in range(-radius, radius + 1):
            for dz in range(-radius, radius + 1):
                if abs(dx) == radius or abs(dz) == radius:
                    self.renderer.set_block(
                        center.offset(dx, -1, dz),
                        "smooth_quartz_slab",
                    )

    def _render_tool_ring(
        self,
        tools: list["MCPToolState"],
        center: Position,
    ) -> None:
        """渲染工具环"""
        radius = self.config.tool_ring_radius
        num_tools = min(len(tools), self.config.max_tools_per_ring)

        if num_tools == 0:
            return

        angle_step = 360 / num_tools

        for i, tool in enumerate(tools[:num_tools]):
            angle = math.radians(i * angle_step)
            x = int(radius * math.cos(angle))
            z = int(radius * math.sin(angle))
            pos = center.offset(x, 0, z)

            # 记录位置
            self._tool_positions[tool.name] = pos

            # 方块
            block = BlockType.MCP_TOOL_ACTIVE if tool.is_active else BlockType.MCP_TOOL
            self.renderer.set_block(pos, block)

            # 标签
            if self.config.show_labels:
                short_name = tool.name[:10] if len(tool.name) > 10 else tool.name
                self.renderer.summon_armor_stand(
                    pos.offset(dy=1),
                    f"§7{short_name}",
                )

    def _render_tower_top(self, center: Position) -> None:
        """渲染塔顶"""
        # 尖顶
        self.renderer.set_block(center, "beacon")
        self.renderer.set_block(center.offset(dy=1), "lightning_rod")

        # 信标底座
        for dx in range(-1, 2):
            for dz in range(-1, 2):
                self.renderer.set_block(
                    center.offset(dx, -1, dz),
                    "iron_block",
                )

    def highlight_server(
        self,
        server_name: str,
        duration_seconds: int = 5,
    ) -> list[str]:
        """高亮指定 Server"""
        self.renderer.clear_commands()

        if server_name in self._server_positions:
            pos = self._server_positions[server_name]
            self.renderer.particle(
                "minecraft:totem_of_undying",
                pos.offset(dy=1),
                count=50,
                spread=2,
            )

        return self.renderer.get_commands()

    def highlight_tool(
        self,
        tool_name: str,
    ) -> list[str]:
        """高亮指定工具"""
        self.renderer.clear_commands()

        if tool_name in self._tool_positions:
            pos = self._tool_positions[tool_name]
            self.renderer.set_block(pos, BlockType.MCP_TOOL_ACTIVE)
            self.renderer.particle(
                "minecraft:happy_villager",
                pos.offset(dy=0.5),
                count=20,
            )

        return self.renderer.get_commands()

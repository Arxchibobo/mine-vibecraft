"""
Claude Code Visualizer - VibeCraft Extension

将 Minecraft 变成 Claude Code 的实时 3D 控制室，展示：
- Skills Matrix (技能矩阵)
- MCP Tower (MCP 塔)
- Plugins Garden (插件花园)
- Agent Timeline (进度时间线)
- Central Hub (中央枢纽)
"""

from .state import VisualizerState
from .renderer import MinecraftRenderer
from .event_receiver import EventReceiver
from .hooks_config import (
    generate_hooks_config,
    install_hooks_config,
)
from .layouts import (
    SkillsMatrixLayout,
    MCPTowerLayout,
    PluginsGardenLayout,
    AgentTimelineLayout,
    CentralHubLayout,
)

__all__ = [
    "VisualizerState",
    "MinecraftRenderer",
    "EventReceiver",
    "generate_hooks_config",
    "install_hooks_config",
    "SkillsMatrixLayout",
    "MCPTowerLayout",
    "PluginsGardenLayout",
    "AgentTimelineLayout",
    "CentralHubLayout",
]

__version__ = "0.1.0"

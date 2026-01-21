"""
Claude Code Hooks Configuration Generator

生成用于集成 Claude Code 与 VibeCraft Visualizer 的 hooks.json 配置
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def generate_hooks_config(
    visualizer_url: str = "http://localhost:8767",
) -> dict[str, Any]:
    """
    生成 Claude Code hooks.json 配置

    这个配置会将 Claude Code 的事件通过 HTTP POST 发送到 Visualizer

    Args:
        visualizer_url: Visualizer HTTP 服务器地址

    Returns:
        hooks.json 配置字典
    """
    return {
        "version": "1.0",
        "description": "VibeCraft Visualizer hooks for Claude Code",
        "hooks": {
            # Tool 调用事件
            "PostToolUse": [
                {
                    "type": "command",
                    "command": f'curl -s -X POST {visualizer_url}/event -H "Content-Type: application/json" -d \'{{"event_type": "tool_call", "payload": {{"tool": "$TOOL_NAME", "input": "$TOOL_INPUT_PREVIEW"}}}}\'',
                    "background": True,
                    "timeout": 5000,
                }
            ],
            # Skill 调用事件
            "PreSkillUse": [
                {
                    "type": "command",
                    "command": f'curl -s -X POST {visualizer_url}/event -H "Content-Type: application/json" -d \'{{"event_type": "skill_invoke", "payload": {{"skill": "$SKILL_NAME"}}}}\'',
                    "background": True,
                    "timeout": 5000,
                }
            ],
            # Skill 完成事件
            "PostSkillUse": [
                {
                    "type": "command",
                    "command": f'curl -s -X POST {visualizer_url}/event -H "Content-Type: application/json" -d \'{{"event_type": "skill_complete", "payload": {{"skill": "$SKILL_NAME"}}}}\'',
                    "background": True,
                    "timeout": 5000,
                }
            ],
            # Agent 创建事件
            "PostAgentCreate": [
                {
                    "type": "command",
                    "command": f'curl -s -X POST {visualizer_url}/event -H "Content-Type: application/json" -d \'{{"event_type": "agent_spawn", "payload": {{"agent_id": "$AGENT_ID", "agent_type": "$AGENT_TYPE"}}}}\'',
                    "background": True,
                    "timeout": 5000,
                }
            ],
            # 错误事件
            "OnError": [
                {
                    "type": "command",
                    "command": f'curl -s -X POST {visualizer_url}/event -H "Content-Type: application/json" -d \'{{"event_type": "error", "payload": {{"error_type": "runtime", "message": "$ERROR_MESSAGE"}}}}\'',
                    "background": True,
                    "timeout": 5000,
                }
            ],
        },
    }


def generate_hooks_config_powershell(
    visualizer_url: str = "http://localhost:8767",
) -> dict[str, Any]:
    """
    生成 Windows PowerShell 版本的 hooks.json 配置

    Args:
        visualizer_url: Visualizer HTTP 服务器地址

    Returns:
        hooks.json 配置字典
    """
    return {
        "version": "1.0",
        "description": "VibeCraft Visualizer hooks for Claude Code (Windows PowerShell)",
        "hooks": {
            # Tool 调用事件
            "PostToolUse": [
                {
                    "type": "command",
                    "command": f'powershell -Command "Invoke-RestMethod -Uri \'{visualizer_url}/event\' -Method Post -ContentType \'application/json\' -Body \'{{\\\"event_type\\\": \\\"tool_call\\\", \\\"payload\\\": {{\\\"tool\\\": \\\"$TOOL_NAME\\\"}}}}\'"',
                    "background": True,
                    "timeout": 5000,
                }
            ],
            # Skill 调用事件
            "PreSkillUse": [
                {
                    "type": "command",
                    "command": f'powershell -Command "Invoke-RestMethod -Uri \'{visualizer_url}/event\' -Method Post -ContentType \'application/json\' -Body \'{{\\\"event_type\\\": \\\"skill_invoke\\\", \\\"payload\\\": {{\\\"skill\\\": \\\"$SKILL_NAME\\\"}}}}\'"',
                    "background": True,
                    "timeout": 5000,
                }
            ],
            # Skill 完成事件
            "PostSkillUse": [
                {
                    "type": "command",
                    "command": f'powershell -Command "Invoke-RestMethod -Uri \'{visualizer_url}/event\' -Method Post -ContentType \'application/json\' -Body \'{{\\\"event_type\\\": \\\"skill_complete\\\", \\\"payload\\\": {{\\\"skill\\\": \\\"$SKILL_NAME\\\"}}}}\'"',
                    "background": True,
                    "timeout": 5000,
                }
            ],
            # Agent 创建事件
            "PostAgentCreate": [
                {
                    "type": "command",
                    "command": f'powershell -Command "Invoke-RestMethod -Uri \'{visualizer_url}/event\' -Method Post -ContentType \'application/json\' -Body \'{{\\\"event_type\\\": \\\"agent_spawn\\\", \\\"payload\\\": {{\\\"agent_id\\\": \\\"$AGENT_ID\\\", \\\"agent_type\\\": \\\"$AGENT_TYPE\\\"}}}}\'"',
                    "background": True,
                    "timeout": 5000,
                }
            ],
        },
    }


def install_hooks_config(
    hooks_dir: Path | None = None,
    visualizer_url: str = "http://localhost:8767",
    platform: str = "unix",
) -> Path:
    """
    安装 hooks.json 到 Claude Code 配置目录

    Args:
        hooks_dir: Claude Code hooks 目录，默认 ~/.claude/
        visualizer_url: Visualizer HTTP 服务器地址
        platform: 平台 ("unix" 或 "windows")

    Returns:
        生成的配置文件路径
    """
    if hooks_dir is None:
        hooks_dir = Path.home() / ".claude"

    hooks_dir.mkdir(parents=True, exist_ok=True)
    hooks_file = hooks_dir / "hooks.json"

    if platform == "windows":
        config = generate_hooks_config_powershell(visualizer_url)
    else:
        config = generate_hooks_config(visualizer_url)

    with open(hooks_file, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    return hooks_file


def print_hooks_config(platform: str = "unix") -> None:
    """打印 hooks 配置到控制台"""
    if platform == "windows":
        config = generate_hooks_config_powershell()
    else:
        config = generate_hooks_config()

    print(json.dumps(config, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    import sys

    platform = "windows" if sys.platform == "win32" else "unix"
    print(f"Claude Code Hooks Configuration ({platform}):")
    print("=" * 60)
    print_hooks_config(platform)
    print("=" * 60)
    print(f"\nTo install, run:")
    print(f"  python -c \"from vibecraft.visualizer.hooks_config import install_hooks_config; install_hooks_config(platform='{platform}')\"")

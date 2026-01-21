"""
Event Receiver

HTTP 服务器，接收来自 Claude Code Hooks 的事件：
- tool_call: 工具调用
- skill_invoke: Skill 调用
- agent_spawn: Agent 创建
- todo_update: Todo 列表更新
- error: 错误发生
"""

from __future__ import annotations

import asyncio
import json
import logging
import threading
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from .state import VisualizerState

logger = logging.getLogger(__name__)


@dataclass
class Event:
    """事件数据"""
    type: str
    payload: dict[str, Any]
    timestamp: float


class EventHandler:
    """
    事件处理器

    将接收到的事件路由到对应的状态更新方法
    """

    def __init__(self, state: "VisualizerState"):
        self.state = state
        self._callbacks: list[Callable[[Event], None]] = []

    def register_callback(self, callback: Callable[[Event], None]) -> None:
        """注册事件回调"""
        self._callbacks.append(callback)

    def handle_event(self, event: Event) -> None:
        """处理事件"""
        logger.info(f"Handling event: {event.type}")

        if event.type == "tool_call":
            self._handle_tool_call(event.payload)
        elif event.type == "skill_invoke":
            self._handle_skill_invoke(event.payload)
        elif event.type == "skill_complete":
            self._handle_skill_complete(event.payload)
        elif event.type == "agent_spawn":
            self._handle_agent_spawn(event.payload)
        elif event.type == "agent_complete":
            self._handle_agent_complete(event.payload)
        elif event.type == "todo_update":
            self._handle_todo_update(event.payload)
        elif event.type == "error":
            self._handle_error(event.payload)
        elif event.type == "mcp_status":
            self._handle_mcp_status(event.payload)
        else:
            logger.warning(f"Unknown event type: {event.type}")

        # 触发回调
        for callback in self._callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Callback error: {e}")

    def _handle_tool_call(self, payload: dict[str, Any]) -> None:
        """处理工具调用"""
        tool_name = payload.get("tool", "unknown")
        server = payload.get("server")
        self.state.handle_tool_call(tool_name, server)

    def _handle_skill_invoke(self, payload: dict[str, Any]) -> None:
        """处理 Skill 调用"""
        skill_name = payload.get("skill", "unknown")
        self.state.handle_skill_invoke(skill_name)

    def _handle_skill_complete(self, payload: dict[str, Any]) -> None:
        """处理 Skill 完成"""
        skill_name = payload.get("skill", "unknown")
        self.state.handle_skill_complete(skill_name)

    def _handle_agent_spawn(self, payload: dict[str, Any]) -> None:
        """处理 Agent 创建"""
        agent_id = payload.get("agent_id", "unknown")
        agent_type = payload.get("agent_type", "general")
        description = payload.get("description", "")
        self.state.handle_agent_spawn(agent_id, agent_type, description)

    def _handle_agent_complete(self, payload: dict[str, Any]) -> None:
        """处理 Agent 完成"""
        agent_id = payload.get("agent_id", "unknown")
        self.state.handle_agent_complete(agent_id)

    def _handle_todo_update(self, payload: dict[str, Any]) -> None:
        """处理 Todo 更新"""
        todos = payload.get("todos", [])
        self.state.handle_todo_update(todos)

    def _handle_error(self, payload: dict[str, Any]) -> None:
        """处理错误"""
        error_type = payload.get("error_type", "unknown")
        message = payload.get("message", "")
        self.state.handle_error(error_type, message)

    def _handle_mcp_status(self, payload: dict[str, Any]) -> None:
        """处理 MCP 状态变化"""
        server_name = payload.get("server", "unknown")
        status = payload.get("status", "offline")
        self.state.handle_mcp_status(server_name, status)


class EventReceiverHTTPHandler(BaseHTTPRequestHandler):
    """HTTP 请求处理器"""

    # 类级别的事件处理器引用
    event_handler: EventHandler | None = None

    def log_message(self, format: str, *args) -> None:
        """重写日志方法"""
        logger.debug(f"HTTP: {format % args}")

    def do_POST(self) -> None:
        """处理 POST 请求"""
        if self.path != "/event":
            self.send_error(404, "Not Found")
            return

        try:
            # 读取请求体
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode("utf-8"))

            # 创建事件
            event = Event(
                type=data.get("type", "unknown"),
                payload=data.get("payload", {}),
                timestamp=data.get("timestamp", 0),
            )

            # 处理事件
            if self.event_handler:
                self.event_handler.handle_event(event)

            # 返回成功响应
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True}).encode("utf-8"))

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON: {e}")
            self.send_error(400, f"Invalid JSON: {e}")
        except Exception as e:
            logger.error(f"Error processing event: {e}")
            self.send_error(500, f"Internal error: {e}")

    def do_GET(self) -> None:
        """处理 GET 请求 (健康检查)"""
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode("utf-8"))
        else:
            self.send_error(404, "Not Found")


class EventReceiver:
    """
    事件接收器

    运行 HTTP 服务器接收 Claude Code Hooks 事件
    """

    def __init__(
        self,
        state: "VisualizerState",
        host: str = "127.0.0.1",
        port: int = 8767,
    ):
        self.state = state
        self.host = host
        self.port = port
        self.event_handler = EventHandler(state)
        self._server: HTTPServer | None = None
        self._server_thread: threading.Thread | None = None
        self._running = False

    def start(self) -> None:
        """启动事件接收器"""
        if self._running:
            logger.warning("Event receiver already running")
            return

        # 设置类级别的处理器引用
        EventReceiverHTTPHandler.event_handler = self.event_handler

        # 创建 HTTP 服务器
        self._server = HTTPServer((self.host, self.port), EventReceiverHTTPHandler)

        # 在后台线程运行
        self._running = True
        self._server_thread = threading.Thread(
            target=self._run_server,
            daemon=True,
            name="EventReceiver",
        )
        self._server_thread.start()
        logger.info(f"Event receiver started on {self.host}:{self.port}")

    def _run_server(self) -> None:
        """运行服务器循环"""
        while self._running and self._server:
            self._server.handle_request()

    def stop(self) -> None:
        """停止事件接收器"""
        self._running = False
        if self._server:
            self._server.shutdown()
            self._server = None
        logger.info("Event receiver stopped")

    def register_callback(self, callback: Callable[[Event], None]) -> None:
        """注册事件回调"""
        self.event_handler.register_callback(callback)


# ===== Claude Code Hooks 配置生成 =====


def generate_hooks_config(
    event_receiver_url: str = "http://127.0.0.1:8767/event",
) -> dict[str, Any]:
    """
    生成 Claude Code Hooks 配置

    用于 ~/.claude/hooks.json
    """
    return {
        "hooks": {
            # 工具调用事件
            "PreToolUse": [
                {
                    "matcher": ".*",
                    "hooks": [
                        {
                            "type": "command",
                            "command": f'curl -s -X POST {event_receiver_url} -H "Content-Type: application/json" -d "{{\\"type\\":\\"tool_call\\",\\"payload\\":{{\\"tool\\":\\"$TOOL_NAME\\"}}}}"',
                        }
                    ],
                }
            ],
            # Skill 调用事件
            "PreSkillUse": [
                {
                    "matcher": ".*",
                    "hooks": [
                        {
                            "type": "command",
                            "command": f'curl -s -X POST {event_receiver_url} -H "Content-Type: application/json" -d "{{\\"type\\":\\"skill_invoke\\",\\"payload\\":{{\\"skill\\":\\"$SKILL_NAME\\"}}}}"',
                        }
                    ],
                }
            ],
        }
    }


def generate_hooks_config_windows(
    event_receiver_url: str = "http://127.0.0.1:8767/event",
) -> dict[str, Any]:
    """
    生成 Windows 兼容的 Claude Code Hooks 配置

    使用 PowerShell 的 Invoke-WebRequest
    """
    return {
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": ".*",
                    "hooks": [
                        {
                            "type": "command",
                            "command": f'powershell -Command "Invoke-WebRequest -Uri \'{event_receiver_url}\' -Method POST -ContentType \'application/json\' -Body \'{{\\"type\\":\\"tool_call\\",\\"payload\\":{{\\"tool\\":\\"$TOOL_NAME\\"}}}}\'"',
                        }
                    ],
                }
            ],
        }
    }

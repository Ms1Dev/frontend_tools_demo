import json
import threading

from .events import publish

_lock = threading.Lock()
_tools: dict[str, dict] = {}


def register_tools(tools: list[dict]) -> None:
    with _lock:
        for tool in tools:
            _tools[tool["name"]] = tool


def get_tools() -> list[dict]:
    with _lock:
        return list(_tools.values())


def is_frontend_tool(name: str) -> bool:
    with _lock:
        return name in _tools


def to_openai_tools() -> list[dict]:
    return [
        {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": {
                    "type": "object",
                    "properties": {
                        k: {"type": v["type"], "description": v.get("description", "")}
                        for k, v in tool.get("params", {}).items()
                    },
                    "required": list(tool.get("params", {}).keys()),
                },
            },
        }
        for tool in get_tools()
    ]


def execute(name: str, arguments: dict) -> str:
    publish({"type": "tool_call", "tool": name, "args": arguments})
    return json.dumps({"status": "dispatched"})

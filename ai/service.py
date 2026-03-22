import json
import os
from typing import Generator

from openai import OpenAI

from relay.events import publish
from .tools import TOOLS, execute_tool

MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
_client = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return _client


def _to_openai(tools: list[dict]) -> list[dict]:
    return [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": {
                    "type": "object",
                    "properties": {
                        k: {"type": v["type"], "description": v.get("description", "")}
                        for k, v in t.get("params", {}).items()
                    },
                    "required": list(t.get("params", {}).keys()),
                },
            },
        }
        for t in tools
    ]


def _execute(name: str, arguments: dict, frontend_tool_names: set[str]) -> str:
    if name in frontend_tool_names:
        publish({"type": "tool_call", "tool": name, "args": arguments})
        return json.dumps({"status": "dispatched"})
    return execute_tool(name, arguments)


SYSTEM_PROMPT = """You are a helpful assistant with access to a task management app.

When working through a request, use the `log` tool to narrate your thinking — what you're about to do, decisions you're making, and results of actions. Keep log messages short and clear.

To manage tasks use: list_tasks, add_task, delete_task.
After any add or delete, always call refresh_task_list so the UI updates."""


def stream_response(history: list[dict], frontend_tools: list[dict]) -> Generator[str, None, str]:
    """Stream an LLM response, handling tool calls transparently.

    Yields text chunks as they arrive and returns the full assembled response.
    """
    client = get_client()
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + list(history)
    all_tools = TOOLS + _to_openai(frontend_tools)
    frontend_tool_names = {t["name"] for t in frontend_tools}
    full_response = []

    while True:
        stream = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            stream=True,
            **({"tools": all_tools} if all_tools else {}),
        )

        text_chunks: list[str] = []
        tool_calls: dict[int, dict] = {}
        finish_reason = None

        for chunk in stream:
            choice = chunk.choices[0]
            finish_reason = choice.finish_reason or finish_reason
            delta = choice.delta

            if delta.content:
                text_chunks.append(delta.content)
                full_response.append(delta.content)
                yield delta.content

            if delta.tool_calls:
                for tc in delta.tool_calls:
                    if tc.index not in tool_calls:
                        tool_calls[tc.index] = {"id": tc.id, "name": tc.function.name, "arguments": ""}
                    if tc.function.arguments:
                        tool_calls[tc.index]["arguments"] += tc.function.arguments

        if finish_reason != "tool_calls":
            break

        messages.append({
            "role": "assistant",
            "content": "".join(text_chunks) or None,
            "tool_calls": [
                {
                    "id": tc["id"],
                    "type": "function",
                    "function": {"name": tc["name"], "arguments": tc["arguments"]},
                }
                for tc in tool_calls.values()
            ],
        })

        for tc in tool_calls.values():
            result = _execute(tc["name"], json.loads(tc["arguments"]), frontend_tool_names)
            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": result,
            })

    return "".join(full_response)

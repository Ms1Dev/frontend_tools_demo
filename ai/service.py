import json
import os
from typing import Generator

from openai import OpenAI

from .tools import TOOLS, execute_tool

_client = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return _client


def stream_response(history: list[dict]) -> Generator[str, None, str]:
    """Stream an LLM response, handling tool calls transparently.

    Yields text chunks as they arrive and returns the full assembled response.
    """
    client = get_client()
    messages = list(history)
    full_response = []

    while True:
        stream = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=TOOLS,
            stream=True,
        )

        # Accumulate this turn's text and tool calls
        text_chunks: list[str] = []
        tool_calls: dict[int, dict] = {}  # index -> {id, name, arguments}
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

        # Append the assistant turn (with tool_calls) to history
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

        # Execute each tool and append results
        for tc in tool_calls.values():
            result = execute_tool(tc["name"], json.loads(tc["arguments"]))
            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": result,
            })

    return "".join(full_response)

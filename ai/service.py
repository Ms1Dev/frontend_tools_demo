import os
from typing import Generator

from openai import OpenAI

_client = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return _client


def stream_response(history: list[dict]) -> Generator[str, None, str]:
    """Stream an LLM response for the given message history.

    Yields text chunks as they arrive and returns the full assembled response.
    """
    client = get_client()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=history,
        stream=True,
    )

    full_response = []
    for chunk in response:
        text = chunk.choices[0].delta.content
        if text:
            full_response.append(text)
            yield text

    return "".join(full_response)

# LLM Notes App Demo

A Django app that gives an LLM tools front end tooling so it can update the UI.

When the LLM calls a browser tool, the server publishes it as an SSE event. One browser tab holds the SSE connection (coordinated via `navigator.locks` so multiple tabs don't compete), and forwards events to other tabs via `BroadcastChannel`.


## Running

Copy `.env.example` to `.env`, add your OpenAI API key, then:

```
docker compose up --build
```

---

## Adding a browser tool

Browser tools are defined in two places:

**1. Schema — `ai/frontend_tools.py`**

Add an entry to `FRONTEND_TOOLS` in OpenAI function format:

```python
{
    "type": "function",
    "function": {
        "name": "highlight_note",
        "description": "Highlight a note in the list to draw the user's attention to it.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {"type": "integer", "description": "The note ID to highlight"},
            },
            "required": ["id"],
        },
    },
},
```

**2. Handler — `notes/templates/notes/index.html`**

Add a `.on()` call in the relay block:

```js
window._relay = new Relay()
  ...
  .on('highlight_note', ({ id }) => {
    document.querySelector(`.note-item[data-id="${id}"]`)?.classList.add('highlighted')
  })
  .connect()
```

When the LLM calls the tool, the server dispatches it via SSE and the handler runs in the browser.

---

## Production considerations

This is a proof of concept. Before using it as a base for anything real:

**SSE is a global broadcast.** `relay/events.py` uses a single in-memory client list — every connected browser receives every tool call. In a multi-user deployment you need per-user or per-session queues, keyed to the authenticated user. The routing change is small; the prerequisite is adding auth.

**The event queue is in-memory.** Tool call events are lost on server restart and won't work across multiple processes. Replace the queue in `relay/events.py` with Redis pub/sub for production.

**The model is configurable.** Set `OPENAI_MODEL` in your environment. Defaults to `gpt-4o-mini`. Its recommended to use more capable models as they handle parallel and sequential tool calls more reliably.

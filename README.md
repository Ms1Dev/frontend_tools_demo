# LLM Task App Demo

A Django app demonstrating how to give an LLM tools that run directly in the browser.

## To run

Make a .env file based off the example and add your openai api key. Run compose:

```
docker compose up --build
```

---

## Registering front-end tools

Front-end tools are defined in the page's relay module block. Each tool has a name, a description the LLM uses to decide when to call it, the parameters it accepts, and a `fn` that runs in the browser when the LLM calls it.

```js
// index.html
import { Relay } from '/static/relay.js'

window._relay = new Relay()
  .register({
    name: 'drop_pin',
    description: 'Drop a marker pin on the map at the given coordinates with an optional label.',
    params: {
      lat:   { type: 'number', description: 'Latitude' },
      lng:   { type: 'number', description: 'Longitude' },
      label: { type: 'string', description: 'Popup label shown on the pin (optional)' },
    },
    fn: ({ lat, lng, label = '' }) => {
      if (!window.map) return
      const marker = L.marker([lat, lng]).addTo(window.map)
      if (label) marker.bindPopup(label).openPopup()
      window.map.flyTo([lat, lng], 14)
    },
  })
  .connect()
```

The instance is assigned to `window._relay` so that `chat.js` can call `getSchemas()` when sending a message. Calling `.connect()` opens a persistent SSE connection so the browser can receive tool call events.

### The built-in: `registerHtmxTriggers`

HTMX panel swaps are a common pattern, so the Relay class has a built-in for them. Instead of writing the full `.register()` call, pass an array of trigger descriptors:

```js
window._relay = new Relay()
  .registerHtmxTriggers([
    { name: 'swap-to-map',   description: 'Switch the left panel to the map view' },
    { name: 'swap-to-tasks', description: 'Switch the left panel back to the task list' },
  ])
  .register({ /* other tools */ })
  .connect()
```

This registers a single `htmx_trigger` tool. When the LLM calls it, the relay fires the named DOM event on the element with the matching `data-trigger` attribute, which HTMX picks up and handles.

### Tools belong to the page

Tool registrations live in the page template, not in a shared file. The schema and the `fn` that executes it are defined together. This is intentional — different pages expose different capabilities to the LLM, and the relay is the reusable infrastructure that makes it work anywhere.

---

## How tool schemas reach the LLM

There is no separate registration step. When the user sends a message, `chat.js` includes the tool schemas directly in the POST body:

```js
// chat.js
const body = {
  message,
  tools: window._relay?.getSchemas() ?? [],
}
```

`getSchemas()` returns the schema portion of every registered tool (name, description, params) without the `fn`:

```js
// relay.js
getSchemas() {
  return Array.from(this._tools.values()).map(({ name, description, params }) => ({
    name, description, params,
  }))
}
```

On the server, `ai/views.py` extracts the frontend tool schemas from the request body and passes them to the service layer:

```python
# ai/views.py
frontend_tools = data.get("tools", [])
stream_response(history, frontend_tools)
```

`ai/service.py` combines them with the static backend tools and converts the frontend schemas to OpenAI format:

```python
# ai/service.py
def stream_response(history, frontend_tools):
    all_tools = TOOLS + _to_openai(frontend_tools)
    frontend_tool_names = {t["name"] for t in frontend_tools}
    ...
```

`TOOLS` comes from `ai/tools.py` — a plain list of OpenAI function schemas for server-side operations like `add_task`, `delete_task`, and `list_tasks`. The combined list is passed to the OpenAI API. The LLM sees all tools — server and browser — as equivalent.

---

## How tool calls are routed

When the LLM calls a tool, `ai/service.py` checks whether the name is in the set of frontend tools that came in with the request:

```python
def _execute(name, arguments, frontend_tool_names):
    if name in frontend_tool_names:
        publish({"type": "tool_call", "tool": name, "args": arguments})
        return json.dumps({"status": "dispatched"})
    return execute_tool(name, arguments)
```

**Backend tools** run immediately in Python and return a result. The LLM gets the result and continues reasoning.

**Frontend tools** can't run on the server — they need to run in the browser. So the relay publishes the call as an SSE event and immediately returns `{"status": "dispatched"}` to the LLM. The browser receives it through the persistent SSE connection and executes the registered `fn`:

```js
// relay.js
_dispatch({ tool, args }) {
  this._tools.get(tool)?.fn(args)
}
```

The `fn` runs in the browser with full access to live page state — dropping a pin, switching a panel, writing to the console.

---

## Adding a new front-end tool

Add a `.register()` call in the relay block of your template. Give it a clear `description` — this is what the LLM reads to decide when to use it.

```js
window._relay = new Relay()
  .register({
    name: 'highlight_task',
    description: 'Briefly highlight a task in the list to draw attention to it.',
    params: {
      id: { type: 'number', description: 'The task ID to highlight' },
    },
    fn: ({ id }) => {
      document.querySelector(`.task-item[data-id="${id}"]`)?.classList.add('highlighted')
    },
  })
  .connect()
```

No server changes needed.

---

## Adding a new back-end tool

Add the OpenAI function schema to `TOOLS` in `ai/tools.py` and a handler branch in `execute_tool`:

```python
# ai/tools.py
TOOLS = [
  ...
  {
    "type": "function",
    "function": {
      "name": "complete_task",
      "description": "Mark a task as complete",
      "parameters": {
        "type": "object",
        "properties": {
          "id": {"type": "integer", "description": "Task ID"},
        },
        "required": ["id"],
      },
    },
  },
]

def execute_tool(name, arguments):
  ...
  if name == "complete_task":
      task = Task.objects.get(id=arguments["id"])
      task.completed = True
      task.save()
      return json.dumps({"ok": True})
```

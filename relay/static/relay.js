export class Relay {
  constructor() {
    this._tools = new Map()
    this._handlers = new Map()
    this._channel = new BroadcastChannel('relay')
  }

  // Register a JS function as an LLM-callable tool
  register({ name, description, params, fn }) {
    this._tools.set(name, { name, description, params, fn })
    return this
  }

  // Subscribe to a named SSE event type
  on(type, handler) {
    if (!this._handlers.has(type)) this._handlers.set(type, [])
    this._handlers.get(type).push(handler)
    return this
  }

  // POST schemas to backend and open the SSE connection
  connect() {
    this._sendSchemas()
    this._startSSE()
    return this
  }

  _sendSchemas() {
    const schemas = Array.from(this._tools.values()).map(({ name, description, params }) => ({
      name,
      description,
      params,
    }))
    fetch('/api/relay/register/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tools: schemas }),
    })
  }

  _startSSE() {
    const listenTypes = new Set(['tool_call', ...this._handlers.keys()])

    // navigator.locks ensures only one tab holds the SSE connection
    navigator.locks.request('relay_lock', () => {
      const es = new EventSource('/api/events/')

      listenTypes.forEach((type) => {
        es.addEventListener(type, (event) => {
          const _data = JSON.parse(event.data)
          // Dispatch locally — BroadcastChannel doesn't deliver to the sender
          this._dispatch(type, _data)
          // Notify other tabs
          this._channel.postMessage({ _type: type, _data })
        })
      })

      es.onopen = () => {
        console.log("SSE connection opened");
      }

      es.onerror = () => {
        es.close()
        setTimeout(() => this._startSSE(), 3000)
      }

      // Hold the lock for the lifetime of this tab
      return new Promise(() => {})
    })

    // Other tabs receive via BroadcastChannel
    this._channel.onmessage = ({ data: { _type, _data } }) => {
      this._dispatch(_type, _data)
    }
  }

  _dispatch(type, data) {
    if (type === 'tool_call') this._executeTool(data)
    const handlers = this._handlers.get(type) || []
    handlers.forEach((h) => h(data))
  }

  _executeTool({ tool, args }) {
    const registered = this._tools.get(tool)
    if (registered) registered.fn(args)
  }
}

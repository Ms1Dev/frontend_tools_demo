export class Relay {
  constructor() {
    this._tools = new Map()
    this._channel = new BroadcastChannel('relay')
  }

  // Built-in: register HTMX triggers as a tool
  registerHtmxTriggers(triggers) {
    return this.register({
      name: 'htmx_trigger',
      description: `Fire an HTMX action by name. Available triggers: ${triggers.map(t => `"${t.name}" — ${t.description}`).join('; ')}`,
      params: {
        trigger: { type: 'string', description: `One of: ${triggers.map(t => t.name).join(', ')}` },
      },
      fn: ({ trigger }) => {
        document.querySelector(`[data-trigger="${trigger}"]`)?.dispatchEvent(new Event(trigger))
      },
    })
  }

  // Register a tool: schema (sent to LLM with each request) + fn (executed in browser)
  register({ name, description, params, fn }) {
    this._tools.set(name, { name, description, params, fn })
    return this
  }

  // Return schemas for all registered tools, sent with each chat request
  getSchemas() {
    return Array.from(this._tools.values()).map(({ name, description, params }) => ({
      name, description, params,
    }))
  }

  // Open the SSE connection
  connect() {
    this._startSSE()
    return this
  }

  // ─────────────────────────────────────────────────────
  //
  // Overcoming the issue that some browsers have of only allowing 6 concurrent SSE connections
  // by using navigator.locks to ensure only one tab holds the SSE connection and broadcasting to
  // other tabs via BroadcastChannel.
  //
  // ─────────────────────────────────────────────────────
  _startSSE() {
    // navigator.locks ensures only one tab holds the SSE connection
    navigator.locks.request('relay_lock', () => {
      const es = new EventSource('/api/events/')

      es.addEventListener('tool_call', (event) => {
        const data = JSON.parse(event.data)
        // Dispatch locally — BroadcastChannel doesn't deliver to the sender
        this._dispatch(data)
        // Notify other tabs
        this._channel.postMessage(data)
      })

      es.onerror = () => {
        es.close()
        setTimeout(() => this._startSSE(), 3000)
      }

      // Hold the lock for the lifetime of this tab
      return new Promise(() => {})
    })

    // Other tabs receive via BroadcastChannel
    this._channel.onmessage = ({ data }) => this._dispatch(data)
  }

  // call the tool function with the arguments
  _dispatch({ tool, args }) {
    this._tools.get(tool)?.fn(args)
  }
}

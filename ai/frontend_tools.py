FRONTEND_TOOLS = [
    {
        "name": "htmx_trigger",
        "description": (
            'Fire an HTMX action by name. Available triggers: '
            '"swap-to-map" — Switch the left panel to the map view; '
            '"swap-to-notes" — Switch the left panel back to the note list'
        ),
        "params": {
            "trigger": {"type": "string", "description": "One of: swap-to-map, swap-to-notes"},
        },
    },
    {
        "name": "log",
        "description": "Output a short message to the developer console panel in the UI. Use this to narrate what you are doing.",
        "params": {
            "message": {"type": "string", "description": "Message to display in the console"},
        },
    },
    {
        "name": "refresh_note_list",
        "description": "Reload the note list from the server so the UI reflects the latest data. Call this after any add or delete.",
        "params": {},
    },
    {
        "name": "set_dark_mode",
        "description": "Enable or disable dark mode.",
        "params": {
            "dark": {"type": "boolean", "description": "True to enable dark mode, false to disable"},
        },
    },
    {
        "name": "go_to_coordinates",
        "description": "Pan and zoom the map to a specific location.",
        "params": {
            "lat":  {"type": "number", "description": "Latitude"},
            "lng":  {"type": "number", "description": "Longitude"},
            "zoom": {"type": "number", "description": "Zoom level (default 14)"},
        },
    },
    {
        "name": "drop_pin",
        "description": "Drop a marker on the map at a given location with an optional label.",
        "params": {
            "lat":   {"type": "number", "description": "Latitude"},
            "lng":   {"type": "number", "description": "Longitude"},
            "label": {"type": "string", "description": "Popup label shown on the marker (optional)"},
        },
    },
]

FRONTEND_TOOL_NAMES = {t["name"] for t in FRONTEND_TOOLS}

import json

from tasks.models import Task

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "add_task",
            "description": "Add a new task to the task list",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "The title of the task"},
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_task",
            "description": "Delete a task by its ID",
            "parameters": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "description": "The ID of the task to delete"},
                },
                "required": ["id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_tasks",
            "description": "Return the current list of tasks with their IDs and titles",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]


def execute_tool(name: str, arguments: dict) -> str:
    if name == "add_task":
        title = arguments.get("title", "").strip()
        if not title:
            return json.dumps({"error": "Title required"})
        max_order = Task.objects.order_by("-order").values_list("order", flat=True).first() or 0
        task = Task.objects.create(title=title, order=max_order + 1)
        return json.dumps({"id": task.id, "title": task.title, "order": task.order})

    if name == "delete_task":
        try:
            task = Task.objects.get(id=arguments.get("id"))
            task.delete()
            return json.dumps({"ok": True})
        except Task.DoesNotExist:
            return json.dumps({"error": "Not found"})

    if name == "list_tasks":
        tasks = list(Task.objects.values("id", "title", "order"))
        return json.dumps({"tasks": tasks})

    raise ValueError(f"Unknown tool: {name}")

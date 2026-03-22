import json

from tasks.models import Task
from frontcall.events import publish

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_task",
            "description": "Create a new task in the user's task list.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "The title of the task to create.",
                    }
                },
                "required": ["title"],
            },
        },
    }
]


def execute_tool(name: str, arguments: dict) -> str:
    if name == "create_task":
        max_order = Task.objects.order_by("-order").values_list("order", flat=True).first() or 0
        task = Task.objects.create(title=arguments["title"], order=max_order + 1)
        publish({"type": "task_created", "task": {"id": task.id, "title": task.title, "order": task.order}})
        return json.dumps({"id": task.id, "title": task.title})
    raise ValueError(f"Unknown tool: {name}")

import json
from queue import Queue, Empty

from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .events import register, unregister
from . import registry


def events(request):
    q = Queue()
    register(q)

    def stream():
        try:
            yield "event: connected\ndata: {}\n\n"
            while True:
                try:
                    event = q.get(timeout=25)
                    event_type = event.get("type", "message")
                    yield f"event: {event_type}\ndata: {json.dumps(event)}\n\n"
                except Empty:
                    yield ": heartbeat\n\n"
        finally:
            unregister(q)

    resp = StreamingHttpResponse(stream(), content_type="text/event-stream")
    resp["X-Accel-Buffering"] = "no"
    resp["Cache-Control"] = "no-cache"
    return resp


@csrf_exempt
@require_POST
def register_tools(request):
    data = json.loads(request.body)
    tools = data.get("tools", [])
    registry.register_tools(tools)
    return JsonResponse({"registered": len(tools)})

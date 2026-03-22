import json
import os

from django.http import StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from openai import OpenAI

from tasks.models import Conversation, Message


@csrf_exempt
@require_POST
def chat(request):
    data = json.loads(request.body)
    message_text = data.get("message", "")
    conversation_id = data.get("conversation_id")

    if conversation_id:
        try:
            conversation = Conversation.objects.get(id=conversation_id)
        except Conversation.DoesNotExist:
            conversation = Conversation.objects.create()
    else:
        conversation = Conversation.objects.create()

    Message.objects.create(conversation=conversation, role="user", content=message_text)

    # Auto-title from first message
    if conversation.title == "New Chat":
        conversation.title = message_text[:50]
        conversation.save()

    history = [
        {"role": m.role, "content": m.content}
        for m in conversation.messages.all()
    ]

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    def stream():
        yield f"data: {json.dumps({'conversation_id': conversation.id})}\n\n"

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
                yield f"data: {json.dumps({'text': text})}\n\n"

        Message.objects.create(
            conversation=conversation,
            role="assistant",
            content="".join(full_response),
        )

        yield "data: [DONE]\n\n"

    resp = StreamingHttpResponse(stream(), content_type="text/event-stream")
    resp["X-Accel-Buffering"] = "no"
    resp["Cache-Control"] = "no-cache"
    return resp

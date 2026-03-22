import json
import os
from django.http import StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from openai import OpenAI

@csrf_exempt
@require_POST
def chat(request):
    data = json.loads(request.body)
    message = data.get("message", "")
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    def stream():
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": message}],
            stream=True,
        )
        for chunk in response:
            text = chunk.choices[0].delta.content
            if text:
                yield f"data: {json.dumps({'text': text})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingHttpResponse(stream(), content_type="text/event-stream")

import json
import time

from django.http import JsonResponse, StreamingHttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from .models import Task


def index(request):
    return render(request, 'tasks/index.html')


def task_list(request):
    tasks = list(Task.objects.values('id', 'title', 'order'))
    return JsonResponse({'tasks': tasks})


@require_http_methods(['POST'])
def task_add(request):
    data = json.loads(request.body)
    title = data.get('title', '').strip()
    if not title:
        return JsonResponse({'error': 'Title required'}, status=400)
    max_order = Task.objects.order_by('-order').values_list('order', flat=True).first() or 0
    task = Task.objects.create(title=title, order=max_order + 1)
    return JsonResponse({'id': task.id, 'title': task.title, 'order': task.order})


@require_http_methods(['POST'])
def task_edit(request, task_id):
    data = json.loads(request.body)
    title = data.get('title', '').strip()
    if not title:
        return JsonResponse({'error': 'Title required'}, status=400)
    try:
        task = Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)
    task.title = title
    task.save()
    return JsonResponse({'id': task.id, 'title': task.title, 'order': task.order})


@require_http_methods(['POST'])
def task_delete(request, task_id):
    try:
        task = Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)
    task.delete()
    return JsonResponse({'ok': True})


@require_http_methods(['POST'])
def task_reorder(request):
    data = json.loads(request.body)
    for item in data:
        Task.objects.filter(id=item['id']).update(order=item['order'])
    return JsonResponse({'ok': True})


def chat_stream(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        message = data.get('message', '')
    else:
        message = request.GET.get('message', '')

    def event_stream(msg):
        words = msg.split()
        for i, word in enumerate(words):
            chunk = word + ('' if i == len(words) - 1 else ' ')
            yield f"data: {json.dumps({'text': chunk})}\n\n"
            time.sleep(0.05)
        yield "data: [DONE]\n\n"

    response = StreamingHttpResponse(event_stream(message), content_type='text/event-stream')
    response['X-Accel-Buffering'] = 'no'
    response['Cache-Control'] = 'no-cache'
    return response

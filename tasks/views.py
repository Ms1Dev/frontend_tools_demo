import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from .models import Task, Conversation, Message


def index(request):
    return render(request, 'tasks/index.html')


def panel_tasks(request):
    return render(request, 'tasks/partials/task_panel.html')


def panel_map(request):
    return render(request, 'tasks/partials/map_panel.html')


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


def conversation_list(request):
    convos = list(Conversation.objects.values('id', 'title'))
    return JsonResponse({'conversations': convos})


@require_http_methods(['POST'])
def conversation_create(request):
    convo = Conversation.objects.create()
    return JsonResponse({'id': convo.id, 'title': convo.title})


def conversation_messages(request, convo_id):
    try:
        convo = Conversation.objects.get(id=convo_id)
    except Conversation.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)
    messages = list(convo.messages.values('id', 'role', 'content'))
    return JsonResponse({'messages': messages, 'title': convo.title})

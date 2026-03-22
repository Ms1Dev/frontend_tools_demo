from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/tasks/', views.task_list, name='task-list'),
    path('api/tasks/add/', views.task_add, name='task-add'),
    path('api/tasks/<int:task_id>/edit/', views.task_edit, name='task-edit'),
    path('api/tasks/<int:task_id>/delete/', views.task_delete, name='task-delete'),
    path('api/tasks/reorder/', views.task_reorder, name='task-reorder'),
    path('api/chat/', views.chat_stream, name='chat-stream'),
]

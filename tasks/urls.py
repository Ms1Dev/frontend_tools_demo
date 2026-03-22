from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('panels/tasks/', views.panel_tasks, name='panel-tasks'),
    path('panels/map/', views.panel_map, name='panel-map'),
    path('api/tasks/', views.task_list, name='task-list'),
    path('api/tasks/add/', views.task_add, name='task-add'),
    path('api/tasks/<int:task_id>/edit/', views.task_edit, name='task-edit'),
    path('api/tasks/<int:task_id>/delete/', views.task_delete, name='task-delete'),
    path('api/tasks/reorder/', views.task_reorder, name='task-reorder'),
    path('api/conversations/', views.conversation_list, name='conversation-list'),
    path('api/conversations/create/', views.conversation_create, name='conversation-create'),
    path('api/conversations/<int:convo_id>/messages/', views.conversation_messages, name='conversation-messages'),
]

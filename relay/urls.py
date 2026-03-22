from django.urls import path
from . import views

urlpatterns = [
    path("api/events/", views.events, name="events"),
    path("api/relay/register/", views.register_tools, name="relay-register"),
]

from django.contrib import admin
from django.urls import path
from django.http import HttpResponse


def index(request):
    return HttpResponse("<h1>Demo</h1><p>Django is running.</p>")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", index),
]

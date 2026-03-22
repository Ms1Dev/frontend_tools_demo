from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("notes.urls")),
    path("", include("ai.urls")),
    path("", include("relay.urls")),
]

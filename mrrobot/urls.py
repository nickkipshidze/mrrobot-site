from django.urls import path, include
from django.conf.urls.static import static
from django.http import HttpResponse
from . import views, settings

urlpatterns = [
    path(
        "robots.txt",
        lambda request:
            HttpResponse("User-agent: *\nDisallow: /", content_type="text/plain")
    ),
    
    path("api/", include("api.urls")),
    
    path("", views.viewitem),
    path("view", views.viewitem),
    path("view/<path:path>", views.viewitem, name="view"),
    path("open/<path:path>", views.openitem, name="open"),
    path("stream/<path:path>", views.stream, name="stream"),
    path("watch/<path:path>", views.watch, name="watch"),
    path("database", views.dbstat, name="database"),
    path("server", views.server, name="server"),
    path("about", views.about, name="about"),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
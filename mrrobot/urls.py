from django.urls import path
from django.views.static import serve
from django.conf.urls.static import static
from django.http import HttpResponse
from . import views, settings

urlpatterns = [
    path("robots.txt", lambda request: HttpResponse("User-agent: *\nDisallow: /", content_type="text/plain")),
    path("", views.home),
    path("stream/<path:path>", views.stream, name="stream"),
    path("watch/<path:path>", views.watch, name="watch"),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
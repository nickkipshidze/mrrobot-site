from django.urls import path
from . import views

urlpatterns = [
    path("ping", views.Ping.as_view()),
    path("open/<str:path>", views.Open.as_view())
]
from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("onboarding/", views.onboarding, name="onboarding"),
    path("service-worker.js", views.service_worker, name="service_worker"),
    path("robots.txt", views.robots_txt, name="robots_txt"),
]
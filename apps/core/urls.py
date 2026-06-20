from django.urls import path
from . import views   # use relative import here

app_name = "core"   # ✅ required when using namespace

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
]

# apps/tryon/urls.py
from django.urls import path
from . import views

app_name = 'tryon'

urlpatterns = [
    path('', views.tryon_view, name='index'),
]
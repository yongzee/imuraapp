# apps/tryon/urls.py
from django.urls import path
from . import views

app_name = 'tryon'

urlpatterns = [
    path('', views.tryon_view, name='index'),
    path('initiate/', views.initiate_tryon, name='initiate_tryon'),
    path(
        'status/<str:pred_id>/',
        views.check_tryon_status,
        name='check_tryon_status',
    ),

]
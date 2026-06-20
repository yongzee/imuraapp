from django.urls import path
from . import views

app_name = "streaming"  # ← add this line

urlpatterns = [
    path("products/stream/", views.product_stream, name="product_stream"),
    path("like/<int:video_id>/", views.toggle_like, name="toggle_like"),
    path("comment/<int:video_id>/", views.add_comment, name="add_comment"),
    path("get_comments/<int:video_id>/", views.get_comments, name="get_comments"),
    path('products/trending/', views.trending_stream, name='trending'),
    path('video/<int:video_id>/', views.video_detail, name='video_detail'),
]

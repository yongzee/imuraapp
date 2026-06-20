from django.urls import path
from . import views

app_name = "measureApp"

urlpatterns = [
    path("", views.index, name="index"),
    path("how/", views.how, name="howitworks"),
    path("height/", views.height_input, name="height"),
    path("upload/", views.upload_images, name="upload_image"),
    path("manual_capture/", views.manual_capture, name="manual_capture"),
    path("preview_capture/", views.preview_capture, name="preview_capture"),
    path("submit_capture/", views.submit_capture, name="submit_capture"),
    path("processed_capture/", views.processed_capture, name="processed_capture"),
    path("results/", views.result, name="results"),
    path("share-measurement/", views.share_measurement, name="share_measurement"),
    path("shared/<int:notification_id>/", views.view_shared_measurement, name="view_shared_measurement"),
]

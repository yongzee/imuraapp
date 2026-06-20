from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("profile/<str:username>/", views.profile_view, name="profile"),
    path("edit/", views.profile_edit, name="profile_edit"),
    path("settings/", views.settings_view, name="settings"),
    path("delete/", views.delete_account, name="delete_account"),
    path("users/", views.user_list, name="user_list"),
    path("message/<str:username>/", views.send_message, name="send_message"),
]
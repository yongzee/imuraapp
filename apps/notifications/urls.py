from django.urls import path
from . import views

app_name = "notifications"

urlpatterns = [
    path("", views.notification_list, name="list"),
    path("send_message/", views.send_message, name="send_message"),
    path("propose_price/", views.propose_price, name="propose_price"),
    path("proposal/<int:pk>/accept/", views.proposal_accept, name="proposal_accept"),
    path("proposal/<int:pk>/decline/", views.proposal_decline, name="proposal_decline"),
    path("mark_read/<int:pk>/", views.mark_read, name="mark_read"),
    path('<int:id>/delete/', views.delete_notification, name='delete_notification'),
]
from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path("", views.orders_list, name="list"),
    path("create/<int:product_pk>/", views.create_order, name="create"),
    path("buyer/", views.buyer_orders_list, name="buyer_list"),
    path("seller/", views.seller_orders_list, name="seller_list"),
    path("detail/<int:pk>/", views.order_detail, name="detail"),
    path("checkout/<int:pk>/", views.checkout, name="checkout"),
    path("delete/<int:pk>/", views.delete_order, name="delete"),
    path("verify/<int:pk>/", views.verify_payment, name="verify_payment"),
    path("tracking/buyer/<int:pk>/", views.buyer_tracking, name="buyer_tracking"),
    path("tracking/seller/<int:pk>/", views.seller_tracking, name="seller_tracking"),
    
]



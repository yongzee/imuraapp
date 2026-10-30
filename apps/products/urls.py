from django.urls import path
from . import views

app_name = "products"

urlpatterns = [
    path("post/", views.product_post, name="product_post"),
    path("bulk-post/", views.bulk_create_products, name="bulk_create_products"),
    path("", views.product_list, name="product_list"),
    path("<int:pk>/", views.product_detail, name="product_detail"),
    path("edit/<int:pk>/", views.product_edit, name="product_edit"),
    path("delete/<int:pk>/", views.product_delete, name="product_delete"),
    path('ajax/load-subcategories/', views.load_subcategories, name='ajax_load_subcategories'),
    

]

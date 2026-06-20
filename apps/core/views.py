from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.products.models import Product


def dashboard(request):
    products = Product.objects.all().order_by("-created_at")

    return render(request, "core/dashboard.html", {
        "products": products
    })



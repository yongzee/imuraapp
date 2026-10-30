from django.contrib.sitemaps import Sitemap
from .models import Product
from django.urls import reverse


class PublicProductSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return (
            Product.objects
            .select_related("category")
            .order_by("-created_at")
        )

    def lastmod(self, obj):
        # Product has created_at but no updated_at field.
        return obj.created_at
    



class PublicPageSitemap(Sitemap):
    priority = 1.0
    changefreq = "daily"

    def items(self):
        return ["core:dashboard"]

    def location(self, item):
        return reverse(item)
"""
URL configuration for my_tryon project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.core.views import service_worker, robots_txt
from django.contrib.sitemaps.views import sitemap
from apps.products.sitemaps import PublicProductSitemap, PublicPageSitemap

sitemaps = {
    "pages": PublicPageSitemap,
    "products": PublicProductSitemap,
}
urlpatterns = [
    path("admin/", admin.site.urls), 
    path("accounts/", include("allauth.urls")),
    path("accounts/", include("apps.accounts.urls")), 
    path("", include("apps.core.urls", namespace="core")),  # homepage + dashboard
    path("products/", include("apps.products.urls", namespace="products")),
    path("streaming/", include("apps.streaming.urls", namespace="streaming")),
    path("notifications/", include("apps.notifications.urls", namespace="notifications")),
    path("orders/", include("apps.orders.urls")),
    path('measure/', include("apps.measureApp.urls")),
    path('feedback/', include('apps.feedback.urls')), # Access via /feedback/
    path('tryon/', include('apps.tryon.urls')),
    path("service-worker.js",service_worker,name="service_worker",),
    path("sitemap.xml",sitemap,{"sitemaps": sitemaps},name="django.contrib.sitemaps.views.sitemap",),
    path("robots.txt", robots_txt, name="robots_txt"),
    
    
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
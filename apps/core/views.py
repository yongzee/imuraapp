from django.shortcuts import render
from apps.products.models import Product
from django.contrib.auth.decorators import login_required

from django.http import HttpResponse
from apps.accounts.models import Profile
from django.db.models import Count  
def service_worker(request):
    javascript = """
    const CACHE_NAME = "imura-static-v1";

    self.addEventListener("install", (event) => {
      event.waitUntil(
        caches.open(CACHE_NAME).then((cache) =>
          cache.addAll([
            "/static/pwa/manifest.json",
            "/static/pwa/icons/icon-192.png",
            "/static/pwa/icons/icon-512.png"
          ])
        )
      );
      self.skipWaiting();
    });

    self.addEventListener("activate", (event) => {
      event.waitUntil(
        caches.keys().then((keys) =>
          Promise.all(
            keys
              .filter((key) =>
                key.startsWith("imura-static-") &&
                key !== CACHE_NAME
              )
              .map((key) => caches.delete(key))
          )
        )
      );
      self.clients.claim();
    });

    self.addEventListener("fetch", (event) => {
      const request = event.request;
      const url = new URL(request.url);

      if (
        request.method !== "GET" ||
        url.origin !== self.location.origin ||
        !url.pathname.startsWith("/static/")
      ) {
        return;
      }

      event.respondWith(
        caches.match(request).then((cached) => {
          if (cached) return cached;

          return fetch(request).then((response) => {
            if (response.ok) {
              const copy = response.clone();
              caches.open(CACHE_NAME).then((cache) => {
                cache.put(request, copy);
              });
            }
            return response;
          });
        })
      );
    });
    """

    return HttpResponse(
        javascript,
        content_type="application/javascript",
        headers={"Service-Worker-Allowed": "/"},
    )


def robots_txt(request):
    content = (
        "User-agent: *\n"
        "Allow: /\n"
        "\n"
        "Sitemap: https://imurafh.com.ng/sitemap.xml\n"
    )
    return HttpResponse(content, content_type="text/plain")
  

def dashboard(request):
    products = Product.objects.all().order_by("-created_at")

    # Fetch Boutiques, Fashion Brands & Fabric Vendors (annotated with total product count if available)
    boutique_types = ['fashion_brand', 'fabric_vendor', 'fashion_designer']
    boutiques = Profile.objects.filter(
        user_type__in=boutique_types
    ).select_related('user').annotate(
        product_count=Count('user__products')
    ).order_by('-created_at')[:6]

    # Fetch Tailors
    tailors = Profile.objects.filter(
        user_type='tailor'
    ).select_related('user').order_by('-created_at')[:6]

    return render(request, "core/dashboard.html", {
        "products": products,
        "boutiques": boutiques,
        "tailors": tailors,
    })
    
def onboarding(request):
    return render(request, "core/onboarding.html")
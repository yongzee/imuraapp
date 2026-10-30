import json
import traceback

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction

from .forms import ProductForm
from .models import Product, Category, Subcategory, ProductImage, ProductVideo
from apps.streaming.models import Like, StreamVideo
from apps.notifications.models import Notification


ALLOWED_IMAGE_TYPES = [
    "image/jpeg",
    "image/png",
    "image/webp"
]

ALLOWED_VIDEO_TYPES = [
    "video/mp4",
    "video/quicktime",
    "video/webm",
    "video/3gpp",
    "video/x-msvideo",
    "video/x-matroska",
    "application/octet-stream"
]


@login_required
def product_post(request):
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)

        if form.is_valid():
            image_files = request.FILES.getlist("images")
            video_files = request.FILES.getlist("videos")

            # Require at least one media file
            if not image_files and not video_files:
                messages.error(request, "Upload at least one image or video.")
                return render(
                    request,
                    "products/product_post.html",
                    {"form": form}
                )

            product = form.save(commit=False)
            product.seller = request.user
            product.save()
            form.save_m2m()  # Save M2M relations if any exist

            valid_images = 0
            valid_videos = 0

            # IMAGE UPLOAD
            for img in image_files:
                if not img.content_type.startswith("image"):
                    messages.error(request, f"{img.name} is an invalid image.")
                    continue

                if img.size > 5 * 1024 * 1024:
                    messages.error(request, f"{img.name} is too large (5MB max).")
                    continue

                try:
                    ProductImage.objects.create(
                        product=product,
                        image=img
                    )
                    valid_images += 1
                except Exception as e:
                    messages.error(request, f"{img.name} upload failed: {e}")

            # VIDEO UPLOAD
            allowed_extensions = ["mp4", "mov", "webm", "avi", "mkv", "3gp"]

            for vid in video_files:
                file_ext = vid.name.split('.')[-1].lower()

                # Validate format
                if vid.content_type not in ALLOWED_VIDEO_TYPES and file_ext not in allowed_extensions:
                    messages.error(request, f"{vid.name} has an unsupported format.")
                    continue

                # Validate size
                if vid.size > 50 * 1024 * 1024:
                    messages.error(request, f"{vid.name} is too large (50MB max).")
                    continue

                try:
                    ProductVideo.objects.create(
                        product=product,
                        video=vid
                    )
                    valid_videos += 1
                except Exception as e:
                    print("VIDEO ERROR:", e)
                    messages.error(request, f"{vid.name} failed upload.")

            # If nothing uploaded → cleanup orphaned product instance
            if valid_images == 0 and valid_videos == 0:
                product.delete()
                messages.error(request, "No valid media files were uploaded.")
                return render(
                    request,
                    "products/product_post.html",
                    {"form": form}
                )

            messages.success(
                request,
                f"Product posted successfully ({valid_images} images, {valid_videos} videos)."
            )
            return redirect("products:product_list")

        else:
            messages.error(request, "Please fix the errors in the form.")

    else:
        form = ProductForm()

    return render(
        request,
        "products/product_post.html",
        {"form": form}
    )


@login_required
def product_list(request):
    category_filter = request.GET.get("category")
    subcategory_filter = request.GET.get("subcategory")
    min_price = request.GET.get("min_price")
    max_price = request.GET.get("max_price")
    search_query = request.GET.get("q")

    # Prefetch images & videos so they render instantly without extra DB queries
    products = Product.objects.all().prefetch_related('images', 'videos').order_by("-created_at")

    # FLASH NOTIFICATIONS
    notifications = Notification.objects.filter(
        recipient=request.user,
        read=False
    )

    for n in notifications:
        if n.type == "success":
            messages.success(request, n.verb)
        elif n.type == "warning":
            messages.warning(request, n.verb)
        elif n.type == "error":
            messages.error(request, n.verb)
        else:
            messages.info(request, n.verb)

        n.read = True
        n.save(update_fields=["read"])

    # FILTERS
    if category_filter:
        if category_filter.lower() in ["male", "female"]:
            products = products.filter(category__name__iexact=category_filter)
        elif category_filter.isdigit():
            products = products.filter(category_id=category_filter)

    if subcategory_filter and subcategory_filter.isdigit():
        products = products.filter(subcategory_id=subcategory_filter)

    if min_price:
        products = products.filter(price__gte=min_price)

    if max_price:
        products = products.filter(price__lte=max_price)

    if search_query:
        products = products.filter(title__icontains=search_query)

    liked_products = []
    if request.user.is_authenticated:
        content_type = ContentType.objects.get_for_model(Product)
        liked_ids = Like.objects.filter(
            user=request.user,
            content_type=content_type
        ).values_list("object_id", flat=True)

        liked_products = Product.objects.filter(id__in=liked_ids)

    categories = Category.objects.all()

    return render(request, "products/product_list.html", {
        "products": products,
        "categories": categories,
        "liked_products": liked_products,
        "search_query": search_query,
    })


def product_detail(request, pk):
    product = get_object_or_404(Product.objects.prefetch_related('images', 'videos'), pk=pk)

    images = product.images.all()
    primary_image = images.first()  # Primary garment image for try-on

    videos = StreamVideo.objects.filter(product=product)

    proposed_price = request.GET.get("proposed_price")
    if proposed_price:
        try:
            proposed_price = float(proposed_price)
        except ValueError:
            proposed_price = None

    has_images = images.exists()
    has_videos = videos.exists()

    return render(request, "products/product_detail.html", {
        "product": product,
        "images": images,
        "primary_image": primary_image,
        "videos": videos,
        "proposed_price": proposed_price,
        "has_images": has_images,
        "has_videos": has_videos,
    })


@login_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if product.seller != request.user:
        messages.error(request, "You are not allowed to edit this product.")
        return redirect(product.get_absolute_url())

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            updated_product = form.save()

            # Process new image uploads if provided
            images = request.FILES.getlist("images")
            for img in images:
                ProductImage.objects.create(product=updated_product, image=img)

            # Process new video uploads if provided
            videos = request.FILES.getlist("videos")
            for vid in videos:
                ProductVideo.objects.create(product=updated_product, video=vid)

            messages.success(request, "Product updated successfully.")
            return redirect(updated_product.get_absolute_url())
    else:
        form = ProductForm(instance=product)

    return render(
        request,
        "products/product_edit.html",
        {
            "form": form,
            "product": product,
        },
    )


@login_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if product.seller != request.user:
        messages.error(request, "You are not allowed to delete this product.")
        return redirect(product.get_absolute_url())

    if request.method == "POST":
        product.delete()
        messages.success(request, "Product deleted successfully.")
        return redirect("core:dashboard")

    messages.error(request, "Invalid request.")
    return redirect(product.get_absolute_url())


@login_required
def bulk_create_products(request):
    if request.method == "POST":
        try:
            payload_str = request.POST.get("payload", "{}")
            payload = json.loads(payload_str)
            global_settings = payload.get("global_settings", {})
            products_data = payload.get("products", [])

            if not products_data:
                return JsonResponse(
                    {"status": "error", "message": "No products provided."}, status=400
                )

            # Get valid choices defined on the Product model condition field
            valid_condition_choices = dict(Product._meta.get_field('condition').choices)

            created_products = []

            with transaction.atomic():
                for idx, item in enumerate(products_data):

                    cat_id = item.get("category")
                    category_obj = (
                        Category.objects.filter(id=cat_id).first() if cat_id else None
                    )

                    subcat_id = item.get("subcategory")
                    subcategory_obj = (
                        Subcategory.objects.filter(id=subcat_id).first() if subcat_id else None
                    )

                    # Normalize condition input (e.g., handles "NEW", "new", "New")
                    raw_condition = item.get("condition", "").strip()
                    
                    # Match against valid choices or fall back gracefully
                    if raw_condition in valid_condition_choices:
                        condition_val = raw_condition
                    elif raw_condition.title() in valid_condition_choices:
                        condition_val = raw_condition.title()
                    elif raw_condition.upper() in valid_condition_choices:
                        condition_val = raw_condition.upper()
                    elif raw_condition.lower() in valid_condition_choices:
                        condition_val = raw_condition.lower()
                    else:
                        # Default fallback if choice is completely invalid
                        condition_val = list(valid_condition_choices.keys())[0] if valid_condition_choices else "New"

                    product = Product(
                        seller=request.user,
                        title=item.get("title", "").strip(),
                        brand=item.get("brand", "").strip() or None,
                        category=category_obj,
                        subcategory=subcategory_obj,
                        gender=item.get("gender", "Unisex"),
                        condition=condition_val,
                        size_available=item.get("size_available", "").strip() or None,
                        color=item.get("color", "").strip() or None,
                        price=float(item.get("price") or 0.0),
                        description=item.get("description", "").strip(),
                        shipping_from=global_settings.get("shipping_from", "").strip() or None,
                        delivery_zones=global_settings.get("delivery_zones", "").strip() or None,
                        enable_product_pricing=bool(
                            global_settings.get("enable_product_pricing", True)
                        ),
                        enable_digital_tryon=bool(
                            global_settings.get("enable_digital_tryon", False)
                        ),
                    )
                    
                    # Validate model fields before writing to DB
                    product.full_clean()
                    product.save()

                    # Save uploaded image files
                    image_files = request.FILES.getlist(f"images_product_{idx}")
                    for img_file in image_files:
                        ProductImage.objects.create(
                            product=product, image=img_file
                        )

                    created_products.append(product.id)

            return JsonResponse(
                {"status": "success", "created_count": len(created_products)}
            )

        except Exception as e:
            traceback.print_exc()
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    categories = Category.objects.all()
    return render(request, "products/bulk_post.html", {"categories": categories})

def load_subcategories(request):
    category_id = request.GET.get('category_id')
    if category_id:
        subcategories = Subcategory.objects.filter(
            category_id=category_id
        ).values('id', 'name')
        return JsonResponse(list(subcategories), safe=False)
    return JsonResponse([], safe=False)
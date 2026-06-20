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


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages  # <-- added for notifications

from .forms import ProductForm
from .models import Product, Category, ProductImage, ProductVideo
from apps.streaming.models import Like
from django.contrib import messages
from apps.notifications.models import Notification
from apps.streaming.models import StreamVideo  #  Correct path

@login_required
def product_post(request):

    if request.method == "POST":

        form = ProductForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            image_files = request.FILES.getlist("images")
            video_files = request.FILES.getlist("videos")

            # Require at least one media
            if not image_files and not video_files:

                messages.error(
                    request,
                    "Upload at least one image or video"
                )

                return render(
                    request,
                    "products/product_post.html",
                    {"form": form}
                )

            product = form.save(commit=False)

            product.seller = request.user

            product.save()

            valid_images = 0
            valid_videos = 0

            # IMAGE UPLOAD
            for img in image_files:

                if not img.content_type.startswith("image"):

                    messages.error(
                        request,
                        f"{img.name} invalid image"
                    )
                    continue

                if img.size > 5 * 1024 * 1024:

                    messages.error(
                        request,
                        f"{img.name} too large (5MB max)"
                    )
                    continue

                try:

                    ProductImage.objects.create(
                        product=product,
                        image=img
                    )

                    valid_images += 1

                except Exception as e:

                    messages.error(
                        request,
                        f"{img.name} upload failed"
                    )

            # VIDEO UPLOAD
            for vid in video_files:

                print("VIDEO TYPE:", vid.content_type)
                print("VIDEO NAME:", vid.name)

                file_ext = vid.name.split('.')[-1].lower()

                allowed_extensions = [
                    "mp4",
                    "mov",
                    "webm",
                    "avi",
                    "mkv",
                    "3gp"
                ]

                # Validate format
                if vid.content_type not in ALLOWED_VIDEO_TYPES and file_ext not in allowed_extensions:

                    messages.error(
                        request,
                        f"{vid.name} unsupported format"
                    )

                    continue

                # Validate size
                if vid.size > 50 * 1024 * 1024:

                    messages.error(
                        request,
                        f"{vid.name} too large (50MB max)"
                    )

                    continue

                try:

                    ProductVideo.objects.create(
                        product=product,
                        video=vid
                    )

                    valid_videos += 1

                except Exception as e:

                    print("VIDEO ERROR:", e)

                    messages.error(
                        request,
                        f"{vid.name} failed upload"
                    )

            # If nothing uploaded → delete product
            if valid_images == 0 and valid_videos == 0:

                product.delete()

                messages.error(

                    request,

                    "No valid media uploaded"

                )

                return render(

                    request,

                    "products/product_post.html",

                    {"form": form}

                )

            messages.success(

                request,

                f"Product posted ({valid_images} images, {valid_videos} videos)"

            )

            return redirect("products:product_list")

        else:

            messages.error(
                request,
                "Fix form errors"
            )

    else:

        form = ProductForm()

    return render(

        request,

        "products/product_post.html",

        {"form": form}

    )

@login_required
@login_required
def product_list(request):

    category_filter = request.GET.get("category")
    min_price = request.GET.get("min_price")
    max_price = request.GET.get("max_price")
    search_query = request.GET.get("q")

    products = Product.objects.all().order_by("-created_at")

    # ==============================
    # FLASH NOTIFICATIONS (FIXED)
    # ==============================
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

    # ==============================
    # YOUR EXISTING FILTER LOGIC
    # ==============================
    if category_filter:
        if category_filter.lower() in ["male", "female"]:
            products = products.filter(category__name__iexact=category_filter)
        elif category_filter.isdigit():
            products = products.filter(category_id=category_filter)

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
    product = get_object_or_404(Product, pk=pk)

    # 1. Fetch gallery images
    images = product.images.all()
    
    # 2. Try the explicit filter query first
    try:
        # If your StreamVideo model imports cleanly, keep this:
        from streams.models import StreamVideo # Adjust to your exact app name
        videos = StreamVideo.objects.filter(product=product)
    except (ImportError, NameError):
        # Fallback: dynamically check the model's related managers if import fails
        if hasattr(product, 'videos'):
            videos = product.videos.all()
        elif hasattr(product, 'streamvideo_set'):
            videos = product.streamvideo_set.all()
        else:
            videos = []

    # Check for proposed price query strings
    proposed_price = request.GET.get("proposed_price")
    if proposed_price:
        try:
            proposed_price = float(proposed_price)
        except ValueError:
            proposed_price = None

    # Performance evaluation helper metrics for our template layout engine
    has_images = images.exists() if hasattr(images, 'exists') else bool(images)
    has_videos = videos.exists() if hasattr(videos, 'exists') else bool(videos)

    return render(request, "products/product_detail.html", {
        "product": product,
        "images": images,
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
            form.save()
            messages.success(request, "Product updated successfully.")
            return redirect(product.get_absolute_url())
    else:
        form = ProductForm(instance=product)

    return render(request, "products/product_edit.html", {
        "form": form,
        "product": product,
    })


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


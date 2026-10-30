from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import logout
from django.db.models import Q
from django.contrib.auth import get_user_model

# Update UserForm to CustomSignupForm
# Change your import on line 8 of views.py to import all three forms:
from .forms import UserForm, CustomSignupForm, ProfileForm
from apps.products.models import Product, ProductImage, ProductVideo
from apps.notifications.models import Notification
from apps.products.models import Category, Product, Subcategory # Adjust imports based on your app structure


User = get_user_model()


# ==============================
# PROFILE VIEW
# ==============================
def profile_view(request, username):
    profile_user = get_object_or_404(User, username=username)

    images = ProductImage.objects.filter(
        product__seller=profile_user
    ).select_related("product")

    videos = ProductVideo.objects.filter(
        product__seller=profile_user
    ).select_related("product")

    return render(
        request,
        "account/profile.html",
        {
            "profile_user": profile_user,
            "images": images,
            "videos": videos,
        },
    )


# ==============================
# PROFILE EDIT
# ==============================
@login_required
def profile_edit(request):
    profile = getattr(request.user, "profile", None)
    if not profile:
        messages.error(request, "Profile not found.")
        return redirect("accounts:profile", username=request.user.username)

    if request.method == "POST":
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = ProfileForm(
            request.POST,
            request.FILES,
            instance=profile
        )

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("accounts:profile", username=request.user.username)
    else:
        user_form = UserForm(instance=request.user)
        profile_form = ProfileForm(instance=profile)

    return render(
        request,
        "account/profile_edit.html",
        {
            "user_form": user_form,
            "profile_form": profile_form,
        },
    )


# ==============================
# SETTINGS
# ==============================
@login_required
def settings_view(request):
    return render(request, "account/settings.html")


# ==============================
# DELETE ACCOUNT
# ==============================
@login_required
def delete_account(request):
    if request.method == "POST":
        user = request.user
        username = user.username

        logout(request)
        user.delete()

        messages.success(request, f"Account '{username}' deleted successfully.")
        return redirect("core:home")

    return render(request, "account/delete_account.html")


# ==============================
# USER LIST + SEARCH
# ==============================
def user_list(request):
    query = request.GET.get("q", "").strip()
    active_tab = request.GET.get("tab", "products")
    category_id = request.GET.get("category", "").strip()
    subcategory_id = request.GET.get("subcategory", "").strip()
    min_price = request.GET.get("min_price", "").strip()
    max_price = request.GET.get("max_price", "").strip()

    # 1. Fetch Users & Optimize Profile Relationships
    users = User.objects.select_related("profile").all()

    # 2. Fetch Products with Prefetched Cloudinary Images and Related Models
    products = Product.objects.select_related(
        "seller", "category", "subcategory"
    ).prefetch_related("images").all()

    # 3. Fetch Categories with Subcategories for Sidebar Accordion
    categories = Category.objects.prefetch_related("subcategories").all()

    # 4. Global Search Filter
    if query:
        users = users.filter(
            Q(username__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(profile__bio__icontains=query)
            | Q(profile__location__icontains=query)
            | Q(profile__user_type__icontains=query)
        )
        products = products.filter(
            Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(brand__icontains=query)
            | Q(color__icontains=query)
            | Q(category__name__icontains=query)
            | Q(subcategory__name__icontains=query)
        )

    # 5. Category & Subcategory Filtering
    if subcategory_id:
        if subcategory_id.isdigit():
            products = products.filter(subcategory_id=subcategory_id)
        else:
            products = products.filter(subcategory__name__iexact=subcategory_id)
    elif category_id:
        if category_id.isdigit():
            products = products.filter(category_id=category_id)
        else:
            products = products.filter(
                Q(category__slug=category_id) | Q(category__name__iexact=category_id)
            )

    # 6. Price Range Filtering
    if min_price and min_price.replace(".", "", 1).isdigit():
        products = products.filter(price__gte=float(min_price))
    if max_price and max_price.replace(".", "", 1).isdigit():
        products = products.filter(price__lte=float(max_price))

    # 7. Ordering
    users = users.order_by("username").distinct()
    products = products.order_by("-created_at").distinct()

    # 8. Render Context
    context = {
        "users": users,
        "products": products,
        "categories": categories,
        "query": query,
        "active_tab": active_tab,
    }

    return render(request, "account/user_list.html", context)
# SEND MESSAGE
# ==============================
@login_required
def send_message(request, username):
    recipient = get_object_or_404(User, username=username)

    if recipient == request.user:
        messages.error(request, "You cannot message yourself.")
        return redirect("accounts:profile", username=username)

    if request.method == "POST":
        text = request.POST.get("message", "").strip()

        if not text:
            messages.error(request, "Message cannot be empty.")
            return redirect("accounts:profile", username=username)

        if len(text) > 1000:
            messages.error(request, "Message is too long (max 1000 characters).")
            return redirect("accounts:profile", username=username)

        Notification.objects.create(
            sender=request.user,
            recipient=recipient,
            type="message",
            verb="sent you a message",
            data={"message": text}
        )

        messages.success(request, "Message sent successfully.")
        return redirect("accounts:profile", username=username)

    return redirect("accounts:profile", username=username)
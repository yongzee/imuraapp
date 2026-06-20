from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import logout
from django.db.models import Q
from django.contrib.auth import get_user_model

from .forms import UserForm, ProfileForm
from apps.products.models import ProductImage, ProductVideo
from apps.notifications.models import Notification

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

    users = User.objects.select_related("profile").all()

    if query:
        users = users.filter(
            Q(username__icontains=query) |
            Q(profile__bio__icontains=query) |
            Q(profile__location__icontains=query)
        )

    users = users.order_by("username")

    return render(
        request,
        "account/user_list.html",
        {
            "users": users,
            "query": query,
        },
    )


# ==============================
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
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import UserActivity
from allauth.account.signals import user_signed_up
from .models import Profile

User = get_user_model()


# ===============================
# HELPER FUNCTION
# ===============================
def get_client_ip(request):
    """Get user's IP address safely"""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0]
    return request.META.get("REMOTE_ADDR")


# ===============================
# LOGIN ACTIVITY
# ===============================
@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    if user and request:
        UserActivity.objects.create(
            user=user,
            action="login",
            ip_address=get_client_ip(request),
        )


# ===============================
# LOGOUT ACTIVITY
# ===============================
@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    if user and request:
        UserActivity.objects.create(
            user=user,
            action="logout",
            ip_address=get_client_ip(request),
        )

@receiver(user_signed_up)
def save_easyeasy_referral(sender, request, user, **kwargs):

    profile, created = Profile.objects.get_or_create(
        user=user
    )

    # Preserve the original referral ID.
    subid = request.session.get("easyeasy_subid")

    if subid and not profile.easyeasy_subid:
        profile.easyeasy_subid = subid
        profile.save(
            update_fields=["easyeasy_subid", "updated_at"]
        )

    # Mark this as a newly completed registration.
    # The frontend will consume this flag on the next page.
    request.session["easyeasy_signup_pending"] = {
        "user_id": user.pk
    }

    request.session.modified = True
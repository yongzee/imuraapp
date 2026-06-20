from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import UserActivity

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
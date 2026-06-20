from django.db import models
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

User = get_user_model()


# ===============================
# PROFILE MODEL
# ===============================
class Profile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile"
    )

    avatar = models.ImageField(
        upload_to="avatars/",
        blank=True,
        null=True
    )

    bio = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)

    location = models.CharField(max_length=255, blank=True)

    whatsapp = models.CharField(
        max_length=20,
        blank=True,
        help_text="WhatsApp number e.g +2348012345678"
    )

    instagram = models.URLField(blank=True)
    facebook = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    tiktok = models.URLField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s profile"


# ===============================
# AUTO CREATE / UPDATE PROFILE
# ===============================
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        Profile.objects.get_or_create(user=instance)


# ===============================
# USER ACTIVITY LOG
# ===============================
class UserActivity(models.Model):
    ACTIONS = (
        ("login", "Login"),
        ("logout", "Logout"),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="activities"
    )

    action = models.CharField(max_length=10, choices=ACTIONS)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.action} at {self.timestamp}"
from django.db import models
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import RegexValidator

User = get_user_model()


class Profile(models.Model):

    USER_TYPE_CHOICES = (
        ("customer", "Customer"),
        ("tailor", "Tailor"),
        ("fashion_designer", "Fashion Designer"),
        ("fashion_brand", "Fashion Brand"),
        ("fabric_vendor", "Fabric Vendor"),
        ("others", "Others"),
    )

    NIGERIAN_STATES = (
        ('Abia', 'Abia'),
        ('Adamawa', 'Adamawa'),
        ('Akwa Ibom', 'Akwa Ibom'),
        ('Anambra', 'Anambra'),
        ('Bauchi', 'Bauchi'),
        ('Bayelsa', 'Bayelsa'),
        ('Benue', 'Benue'),
        ('Borno', 'Borno'),
        ('Cross River', 'Cross River'),
        ('Delta', 'Delta'),
        ('Ebonyi', 'Ebonyi'),
        ('Edo', 'Edo'),
        ('Ekiti', 'Ekiti'),
        ('Enugu', 'Enugu'),
        ('Gombe', 'Gombe'),
        ('Imo', 'Imo'),
        ('Jigawa', 'Jigawa'),
        ('Kaduna', 'Kaduna'),
        ('Kano', 'Kano'),
        ('Katsina', 'Katsina'),
        ('Kebbi', 'Kebbi'),
        ('Kogi', 'Kogi'),
        ('Kwara', 'Kwara'),
        ('Lagos', 'Lagos'),
        ('Nasarawa', 'Nasarawa'),
        ('Niger', 'Niger'),
        ('Ogun', 'Ogun'),
        ('Ondo', 'Ondo'),
        ('Osun', 'Osun'),
        ('Oyo', 'Oyo'),
        ('Plateau', 'Plateau'),
        ('Rivers', 'Rivers'),
        ('Sokoto', 'Sokoto'),
        ('Taraba', 'Taraba'),
        ('Yobe', 'Yobe'),
        ('Zamfara', 'Zamfara'),
        ('FCT', 'Federal Capital Territory'),
    )

    phone_validator = RegexValidator(
        regex=r'^\+?\d{10,15}$',
        message="Enter a valid phone number."
    )

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

    bio = models.TextField(
        blank=True,
        max_length=500
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        validators=[phone_validator]
    )

    # Kept fallback to "customer", but registration choices overwrite this immediately
    user_type = models.CharField(
        max_length=30,
        choices=USER_TYPE_CHOICES,
        default="customer"
    )

    state = models.CharField(
        max_length=30,
        choices=NIGERIAN_STATES,
        blank=True
    )

    location = models.CharField(
        max_length=255,
        blank=True
    )

    whatsapp = models.CharField(
        max_length=20,
        blank=True,
        validators=[phone_validator]
    )

    instagram = models.URLField(blank=True)
    facebook = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    tiktok = models.URLField(blank=True)

    # NEW FIELDS

    full_name = models.CharField(
        max_length=120,
        blank=True
    )

    business_name = models.CharField(
        max_length=150,
        blank=True
    )

    verified = models.BooleanField(
        default=False
    )

    profile_completed = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.user.username

    @property
    def completion_percentage(self):
        fields = [
            self.avatar,
            self.bio,
            self.phone,
            self.location,
            self.full_name,
            self.business_name,
            self.whatsapp,
            self.instagram,
            self.facebook,
            self.twitter,
            self.tiktok,
            self.state,
        ]
        completed = sum(bool(field) for field in fields)
        return int((completed / len(fields)) * 100)

    # --- UPDATED SAVE METHOD ---
    def save(self, *args, **kwargs):
        # Automatically flip the completed boolean if percentage hits 100%
        if self.completion_percentage == 100:
            self.profile_completed = True
        else:
            self.profile_completed = False
            
        super().save(*args, **kwargs)
        
        
class UserActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="activities")
    action = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "User Activities"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.user.username} - {self.action} ({self.timestamp.strftime('%Y-%m-%d %H:%M')})"
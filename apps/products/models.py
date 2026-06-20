from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.validators import FileExtensionValidator
from cloudinary.models import CloudinaryField



class Category(models.Model):
    CATEGORY_CHOICES = [
        ('All', 'All'),
        ('Male', 'Male'),
        ('Female', 'Female'),
    ]

    name = models.CharField(max_length=100, choices=CATEGORY_CHOICES, unique=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    CONDITION_CHOICES = [
        ('New', 'New'),
        ('Used', 'Used'),
    ]

    seller = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="products"
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    title = models.CharField(max_length=200)
    brand = models.CharField(max_length=100, null=True, blank=True)

    condition = models.CharField(
        max_length=20,
        choices=CONDITION_CHOICES,
        default="New"
    )

    size_available = models.CharField(max_length=200, blank=True, null=True)
    color = models.CharField(max_length=50, blank=True, null=True)
    shipping_from = models.CharField(max_length=100, blank=True, null=True)
    delivery_zones = models.CharField(max_length=200, blank=True, null=True)

    enable_digital_tryon = models.BooleanField(default=False)
    enable_product_pricing = models.BooleanField(default=True)

    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse("products:product_detail", args=[self.pk])


class ProductImage(models.Model):

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images"
    )

    image = CloudinaryField(
        resource_type="image"
    )

    uploaded_at = models.DateTimeField(auto_now_add=True)

class ProductVideo(models.Model):

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="videos"
    )

    video = CloudinaryField(
        resource_type="video"
    )

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Video for {self.product.title}"
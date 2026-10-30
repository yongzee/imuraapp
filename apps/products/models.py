from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.text import slugify
from cloudinary.models import CloudinaryField
from django.core.exceptions import ValidationError

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True, null=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name) or "category"
            slug = base_slug
            counter = 1
            # Ensure unique slug generation to avoid duplicate key exceptions
            while Category.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

# ... Keep your Category model above ...

class Subcategory(models.Model):
    category = models.ForeignKey(
        Category, 
        on_delete=models.CASCADE, 
        related_name="subcategories"
    )
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name_plural = "Subcategories"
        unique_together = ('category', 'name')
        ordering = ['name']

    def __str__(self):
        return f"{self.category.name} -> {self.name}"


class Product(models.Model):
    CONDITION_CHOICES = [
        ('New', 'New'),
        ('Used', 'Used'),
    ]

    GENDER_CHOICES = [
        ('Unisex', 'Unisex / Universal'),
        ('Women', 'Women'),
        ('Men', 'Men'),
        ('Kids', 'Kids'),
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
        blank=True,
        related_name="products"
    )

    subcategory = models.ForeignKey(
        Subcategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products"
    )

    gender = models.CharField(
        max_length=20,
        choices=GENDER_CHOICES,
        default='Unisex',
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
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        super().clean()
        # Cross-field validation for category/subcategory mapping
        if self.subcategory and self.category:
            if self.subcategory.category_id != self.category_id:
                raise ValidationError({
                    'subcategory': f"Subcategory '{self.subcategory.name}' does not belong to category '{self.category.name}'."
                })

    def save(self, *args, **kwargs):
        # Auto-assign parent category if subcategory is provided alone
        if self.subcategory and not self.category:
            self.category = self.subcategory.category
            
        self.full_clean()
        super().save(*args, **kwargs)

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
    image = CloudinaryField(resource_type="image")
    uploaded_at = models.DateTimeField(auto_now_add=True)


class ProductVideo(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="videos"
    )
    video = CloudinaryField(resource_type="video")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Video for {self.product.title}"
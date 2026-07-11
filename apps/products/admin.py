from django.contrib import admin
from .models import Category, Product, ProductImage, ProductVideo

# --- Inline Layout for Product Images ---
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1  # Provides an empty slot to upload extra images manually if needed
    readonly_fields = ['uploaded_at']

# --- Inline Layout for Product Videos ---
class ProductVideoInline(admin.TabularInline):
    model = ProductVideo
    extra = 1
    readonly_fields = ['uploaded_at']


# --- Main Product Configuration Display panel ---
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    # What columns show up on the main list overview page
    list_display = [
        'title', 
        'seller', 
        'category', 
        'price', 
        'condition', 
        'shipping_from', 
        'enable_digital_tryon', 
        'created_at'
    ]
    
    # Clickable filters on the right sidebar for quick moderation screening
    list_filter = ['category', 'condition', 'enable_digital_tryon', 'created_at', 'shipping_from']
    
    # Global search input properties matching relevant string data
    search_fields = ['title', 'seller__username', 'brand', 'description']
    
    # Pulls the related Images and Videos directly into the product edit workspace page
    inlines = [ProductImageInline, ProductVideoInline]
    
    # Automatically organizes fields inside the update window
    fieldsets = [
        ('Core Listing Details', {
            'fields': ['title', 'seller', 'category', 'description', 'brand']
        }),
        ('Pricing & Inventory metrics', {
            'fields': ['price', 'condition', 'size_available', 'color', 'enable_product_pricing']
        }),
        ('Shipping Operations Logistics', {
            'fields': ['shipping_from', 'delivery_zones']
        }),
        ('Advanced Hub Settings', {
            'fields': ['enable_digital_tryon']
        }),
    ]

    # Deletion safety measures: Standard django admin behavior includes delete actions automatically.
    # Added action confirmation reinforcement checks here.
    actions = ['delete_selected']


# --- Simple Register for Category Choice configuration wheels ---
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
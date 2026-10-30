from django.contrib import admin
from .models import Category, Subcategory, Product, ProductImage, ProductVideo


# --- Inline Layout for Subcategories inside Category ---
class SubcategoryInline(admin.TabularInline):
    model = Subcategory
    extra = 1


# --- Inline Layout for Product Images ---
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    readonly_fields = ['uploaded_at']


# --- Inline Layout for Product Videos ---
class ProductVideoInline(admin.TabularInline):
    model = ProductVideo
    extra = 1
    readonly_fields = ['uploaded_at']


# --- Category Admin Configuration ---
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [SubcategoryInline]


# --- Subcategory Admin Configuration ---
@admin.register(Subcategory)
class SubcategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category']
    list_filter = ['category']
    search_fields = ['name', 'category__name']


# --- Main Product Configuration Display Panel ---
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'seller',
        'category',
        'subcategory',
        'gender',
        'price',
        'condition',
        'shipping_from',
        'enable_digital_tryon',
        'created_at',
    ]

    list_filter = [
        'category',
        'subcategory',
        'gender',
        'condition',
        'enable_digital_tryon',
        'created_at',
        'shipping_from',
    ]

    search_fields = ['title', 'seller__username', 'brand', 'description']

    inlines = [ProductImageInline, ProductVideoInline]

    fieldsets = [
        ('Core Listing Details', {
            'fields': ['title', 'seller', 'category', 'subcategory', 'gender', 'brand', 'description']
        }),
        ('Pricing & Inventory Metrics', {
            'fields': ['price', 'condition', 'size_available', 'color', 'enable_product_pricing']
        }),
        ('Shipping Operations Logistics', {
            'fields': ['shipping_from', 'delivery_zones']
        }),
        ('Advanced Hub Settings', {
            'fields': ['enable_digital_tryon']
        }),
    ]

    actions = ['delete_selected']
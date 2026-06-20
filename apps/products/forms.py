from django import forms
from .models import Product


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "title",
            "brand",
            "condition",
            "size_available",
            "color",
            "shipping_from",
            "delivery_zones",
            "enable_digital_tryon",
            "enable_product_pricing",
            "description",
            "price",
            "category",
        ]

        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter product title"
            }),
            "brand": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter brand"
            }),
            "condition": forms.Select(attrs={
                "class": "form-select"
            }),
            "size_available": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "E.g. M, L, XL or 42, 44"
            }),
            "color": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "E.g. Red, Black"
            }),
            "shipping_from": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "City you're shipping from"
            }),
            "delivery_zones": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Areas you deliver to"
            }),
            "enable_digital_tryon": forms.CheckboxInput(attrs={
                "class": "form-check-input"
            }),
            "enable_product_pricing": forms.CheckboxInput(attrs={
                "class": "form-check-input"
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "placeholder": "Enter product description",
                "rows": 4,
            }),
            "price": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Enter price"
            }),
            "category": forms.Select(attrs={
                "class": "form-select"
            }),
        }

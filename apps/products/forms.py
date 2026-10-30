from django import forms
from .models import Product, Subcategory


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "title",
            "brand",
            "category",
            "subcategory",
            "gender",
            "condition",
            "size_available",
            "color",
            "shipping_from",
            "delivery_zones",
            "description",
            "price",
            "enable_digital_tryon",
            "enable_product_pricing",
        ]

        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. Premium Senator Wear"
            }),
            "brand": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. Tailored / Handmade"
            }),
            "category": forms.Select(attrs={
                "class": "form-select",
                "id": "id_category"
            }),
            "subcategory": forms.Select(attrs={
                "class": "form-select",
                "id": "id_subcategory"
            }),
            "gender": forms.Select(attrs={
                "class": "form-select"
            }),
            "condition": forms.Select(attrs={
                "class": "form-select"
            }),
            "size_available": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. S, M, L, XL or Custom"
            }),
            "color": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. Navy Blue"
            }),
            "shipping_from": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. Lagos, Nigeria"
            }),
            "delivery_zones": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. Nationwide, West Africa"
            }),
            "enable_digital_tryon": forms.CheckboxInput(attrs={
                "class": "switch-input"
            }),
            "enable_product_pricing": forms.CheckboxInput(attrs={
                "class": "switch-input"
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "placeholder": "Describe item material, fit, and key details...",
                "rows": 4,
            }),
            "price": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "0.00"
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Start with an empty subcategory queryset for new forms
        self.fields["subcategory"].queryset = Subcategory.objects.none()

        # Populate subcategories if category data exists in POST or bound instance
        if "category" in self.data:
            try:
                category_id = int(self.data.get("category"))
                self.fields["subcategory"].queryset = Subcategory.objects.filter(
                    category_id=category_id
                ).order_by("name")
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.category:
            self.fields["subcategory"].queryset = (
                self.instance.category.subcategories.order_by("name")
            )
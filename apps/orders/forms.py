from django import forms
from .models import Order


class OrderCreateForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, initial=1)

    buyer_state = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "State"
        })
    )

    buyer_lga = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Local Government"
        })
    )

    buyer_address = forms.CharField(
        widget=forms.Textarea(attrs={
            "rows": 3,
            "class": "form-control",
            "placeholder": "Full delivery address"
        })
    )

    buyer_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            "rows": 2,
            "class": "form-control",
            "placeholder": "Optional note to seller"
        })
    )


class SellerUpdateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            "transport_cost",
            "days_to_deliver",
            "collection_point",   # ✅ ADDED
            "seller_notes",
        ]

        widgets = {
            "transport_cost": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Transport cost (₦)"
            }),
            "days_to_deliver": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Days to deliver"
            }),
            "collection_point": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Where buyer will collect the goods"
            }),
            "seller_notes": forms.Textarea(attrs={
                "rows": 3,
                "class": "form-control",
                "placeholder": "Optional note to buyer"
            }),
        }


class BuyerFeedbackForm(forms.Form):
    ACTION_CHOICES = [
        ("not_satisfactory", "Not satisfactory"),
        ("cancel", "Cancel order"),
    ]

    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.RadioSelect
    )

    feedback = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            "rows": 3,
            "class": "form-control",
            "placeholder": "Explain what needs to be changed"
        })
    )

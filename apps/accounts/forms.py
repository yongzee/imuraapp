from django import forms
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator

from .models import Profile

User = get_user_model()


# -----------------------------
# User Update Form
# -----------------------------
class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "email"]


# -----------------------------
# Custom Signup Form (Allauth compatible)
# -----------------------------
class CustomSignupForm(forms.Form):
    phone = forms.CharField(
        label="Phone Number",
        max_length=20,
        required=True,
        validators=[
            RegexValidator(
                regex=r"^\+?\d{10,15}$",
                message="Enter a valid phone number.",
            )
        ],
        widget=forms.TextInput(attrs={
            "placeholder": "+2348012345678",
            "autocomplete": "tel",
        }),
    )

    user_type = forms.ChoiceField(
        label="I am registering as...",
        choices=Profile.USER_TYPE_CHOICES,
        required=True,
    )

    state = forms.ChoiceField(
        label="State of Residence",
        choices=[("", "Select your state")] + list(Profile.NIGERIAN_STATES),
        required=True,
    )

    agree_terms = forms.BooleanField(
        required=True,
        label="I agree to the Terms of Service and Privacy Policy",
    )

    def signup(self, request, user):
        """
        Allauth automatically calls this method after successfully saving the 
        core User instance. We intercept it here to update the user profile.
        """
        # Ensure a profile object exists or grab it if created by a post_save signal
        profile, created = Profile.objects.get_or_create(user=user)
        
        # Save custom wizard fields safely
        profile.phone = self.cleaned_data["phone"]
        profile.user_type = self.cleaned_data["user_type"]
        profile.state = self.cleaned_data["state"]
        profile.save()


# -----------------------------
# Profile Update Form
# -----------------------------
class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            "avatar",
            "bio",
            "phone",
            "location",
            "whatsapp",
            "instagram",
            "facebook",
            "twitter",
            "tiktok",
        ]

        widgets = {
            "bio": forms.Textarea(attrs={
                "rows": 3,
                "placeholder": "Tell people a little about yourself..."
            }),
            "phone": forms.TextInput(attrs={
                "placeholder": "+2348012345678"
            }),
            "location": forms.TextInput(attrs={
                "placeholder": "City, State"
            }),
            "whatsapp": forms.URLInput(attrs={
                "placeholder": "https://wa.me/234..."
            }),
            "instagram": forms.URLInput(attrs={
                "placeholder": "https://instagram.com/username"
            }),
            "facebook": forms.URLInput(attrs={
                "placeholder": "https://facebook.com/username"
            }),
            "twitter": forms.URLInput(attrs={
                "placeholder": "https://x.com/username"
            }),
            "tiktok": forms.URLInput(attrs={
                "placeholder": "https://tiktok.com/@username"
            }),
        }
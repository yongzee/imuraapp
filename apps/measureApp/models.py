# measureApp/models.py
from django.db import models
from django.conf import settings

class MeasurementProfile(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="measurement_profiles"
    )
    title = models.CharField(max_length=100, help_text="e.g. Summer Suit, Tailored Shirt")
    source = models.CharField(
        max_length=20, 
        choices=[('AI', 'AI Measured'), ('MANUAL', 'Manual Input')], 
        default='MANUAL'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.user.username})"

class MeasurementItem(models.Model):
    profile = models.ForeignKey(
        MeasurementProfile, 
        on_delete=models.CASCADE, 
        related_name="items"
    )
    measure_type = models.CharField(max_length=100, help_text="e.g. Neck, Bicep, Inseam")
    value = models.DecimalField(max_digits=6, decimal_places=2)
    unit = models.CharField(max_length=10, default="inches", choices=[('inches', 'Inches'), ('cm', 'CM')])

    def __str__(self):
        return f"{self.measure_type}: {self.value} {self.unit}"
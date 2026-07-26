# feedback/models.py
from django.db import models

class Feedback(models.Model):
    FEEDBACK_TYPES = [
        ('bug', 'Bug Report'),
        ('feature', 'Feature Request'),
        ('general', 'General Comment'),
    ]

    name = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)  # <-- Added phone field
    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_TYPES, default='general')
    rating = models.PositiveSmallIntegerField(default=5)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_feedback_type_display()} from {self.email or self.phone_number or 'Anonymous'}"
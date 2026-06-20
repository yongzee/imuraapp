from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()

NOTIFICATION_TYPE_CHOICES = [

    ("message","Message"),

    ("price_proposal","Price Proposal"),

    ("measurement_share","Measurement Share"),

    ("info","Info"),

]

class Notification(models.Model):
    """Generic notification between users.

    - sender: user who created the notification
    - recipient: user who should receive it
    - type: message | price_proposal | info
    - verb: short description e.g. "proposed a price"
    - data: JSON payload for extra data (product_id, suggested_price, text)
    - read: whether recipient has read the notification
    - accepted/declined: optional for proposals
    """
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_notifications")
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    type = models.CharField(max_length=32, choices=NOTIFICATION_TYPE_CHOICES, default="info")
    verb = models.CharField(max_length=140)
    data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    # fields for negotiation state (only used for price_proposal)
    accepted = models.BooleanField(null=True, default=None)
    
    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.sender} → {self.recipient}: {self.verb}"

    def get_accept_url(self):
        return reverse("notifications:proposal_accept", args=[self.pk])

    def get_decline_url(self):
        return reverse("notifications:proposal_decline", args=[self.pk])
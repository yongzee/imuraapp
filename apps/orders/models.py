from django.db import models
from django.conf import settings
from django.urls import reverse
from apps.products.models import Product
import uuid
from django.utils import timezone

User = settings.AUTH_USER_MODEL

ORDER_STATUS = [
    ("pending", "Pending (seller review)"),
    ("evaluating", "Evaluating (seller provided costs)"),
    ("completed_by_seller", "Completed by seller (waiting buyer confirm)"),
    ("satisfactory", "Satisfactory (buyer accepted, proceed to checkout)"),
    ("not_satisfactory", "Not satisfactory"),
    ("cancelled", "Cancelled"),
    ("paid", "Paid"),
    ("in_transit", "In transit"),
    ("delivered", "Delivered"),
    ("completed", "Completed"),
]


class Order(models.Model):
    # ================= RELATIONSHIPS =================
    buyer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="orders_made"
    )
    seller = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="orders_received"
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="orders"
    )

    # ================= PRODUCT SNAPSHOT =================
    product_title = models.CharField(max_length=255)
    product_image = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True)

    # ================= ORDER DETAILS =================
    quantity = models.PositiveIntegerField(default=1)
    price_at_order = models.DecimalField(max_digits=12, decimal_places=2)
    suggested_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )

    # ================= BUYER LOCATION =================
    buyer_state = models.CharField(max_length=100, blank=True, null=True)
    buyer_lga = models.CharField(max_length=100, blank=True, null=True)
    buyer_address = models.TextField(blank=True, null=True)

    # ================= SELLER DELIVERY INFO =================
    transport_cost = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    days_to_deliver = models.PositiveIntegerField(null=True, blank=True)

    collection_point = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Where buyer will collect the goods"
    )

    # ================= NOTES =================
    buyer_notes = models.TextField(blank=True, null=True)
    seller_notes = models.TextField(blank=True, null=True)

    # ================= STATUS & TRACKING =================
    status = models.CharField(
        max_length=32, choices=ORDER_STATUS, default="pending"
    )
    is_paid = models.BooleanField(default=False)
    is_sent_to_seller = models.BooleanField(default=False)
    tracking_number = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # 🔐 PAYSTACK FIELDS (NEW)
    payment_reference = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        unique=True
    )
    payment_verified = models.BooleanField(default=False)
    paid_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    payout_released = models.BooleanField(default=False)
    payout_released_at = models.DateTimeField(null=True, blank=True)
    
    extra_days_requested = models.PositiveIntegerField(default=0)
    dispatched_at = models.DateTimeField(null=True, blank=True)
   
    delivery_note = models.TextField(blank=True, null=True)
    delivery_contact = models.CharField(max_length=100, blank=True, null=True)
    delivery_deadline = models.DateTimeField(null=True, blank=True)
    
    seller_bank_name = models.CharField(max_length=100, blank=True, null=True)
    seller_account_name = models.CharField(max_length=100, blank=True, null=True)
    seller_account_number = models.CharField(max_length=20, blank=True, null=True)
    
    payout_receipt = models.FileField(
        upload_to="receipts/",
        blank=True,
        null=True
    )

    payment_verified_by_admin = models.BooleanField(default=False)
    payment_verified_at = models.DateTimeField(null=True, blank=True)
    
    seller_confirmed_payout = models.BooleanField(default=False)
    seller_payout_confirmed_at = models.DateTimeField(blank=True, null=True)

    extension_requested_days = models.PositiveIntegerField(default=0)
    extension_requested_at = models.DateTimeField(null=True, blank=True)
    extension_status = models.CharField(
        max_length=20,
        choices=[
            ("none", "None"),
            ("pending", "Pending"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        default="none"
    )
    
    def save(self, *args, **kwargs):
        if not self.payment_reference:
            self.payment_reference = f"ORD-{uuid.uuid4().hex[:12]}"
        super().save(*args, **kwargs)


    def generate_payment_reference(self):
        return f"ORD-{uuid.uuid4().hex[:12].upper()}"

    def __str__(self):
        return f"Order #{self.pk} — {self.product_title}"

    def get_absolute_url(self):
        return reverse("orders:detail", args=[self.pk])
    
    @property
    def final_price(self):
        return self.suggested_price or self.price_at_order


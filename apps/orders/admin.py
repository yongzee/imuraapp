from django.contrib import admin
from django.utils import timezone
from .models import Order
from apps.notifications.models import Notification


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "product_title",
        "seller",
        "status",
        "is_paid",
        "payment_verified_by_admin",
        "payout_released",
        "seller_confirmed_payout",
    )

    list_filter = (
        "status",
        "is_paid",
        "payment_verified_by_admin",
        "payout_released",
        "seller_confirmed_payout",
    )

    search_fields = (
        "product_title",
        "seller__username",
        "buyer__username",
        "payment_reference",
    )

    # IMPORTANT: Do NOT make bank fields readonly
    readonly_fields = (
        "payment_reference",
        "paid_at",
        "payment_verified_at",
        "payout_released_at",
    )

    fieldsets = (
        ("Order Info", {
            "fields": (
                "buyer",
                "seller",
                "product_title",
                "status",
                "price_at_order",
            )
        }),

        ("Seller Bank Details", {
            "fields": (
                "seller_bank_name",
                "seller_account_name",
                "seller_account_number",
            )
        }),

        ("Admin Payout", {
            "fields": (
                "payout_receipt",
                "payment_verified_by_admin",
                "payment_verified_at",
                "payout_released",
                "payout_released_at",
                "seller_confirmed_payout",
            )
        }),
    )

    actions = [
        "verify_payment_and_notify_seller",
        "mark_payout_completed",
    ]

    # --------------------------------------------------
    # VERIFY PAYMENT + NOTIFY SELLER
    # --------------------------------------------------
    def verify_payment_and_notify_seller(self, request, queryset):
        for order in queryset:
            if order.is_paid and not order.payment_verified_by_admin:
                order.payment_verified_by_admin = True
                order.payment_verified_at = timezone.now()
                order.save()

                Notification.objects.create(
                    sender=request.user,
                    recipient=order.seller,
                    type="success",
                    verb="Admin verified payment. Payout processing started.",
                    data={"order_id": order.id},
                )

        self.message_user(request, "Payment verified. Sellers notified.")

    verify_payment_and_notify_seller.short_description = (
        "✅ Verify payment & notify seller"
    )

    # --------------------------------------------------
    # MARK PAYOUT COMPLETED (AFTER RECEIPT UPLOAD)
    # --------------------------------------------------
    def mark_payout_completed(self, request, queryset):
        for order in queryset:
            if order.payment_verified_by_admin and order.payout_receipt:
                order.payout_released = True
                order.payout_released_at = timezone.now()
                order.save()

                Notification.objects.create(
                    sender=request.user,
                    recipient=order.seller,
                    type="success",
                    verb="Payout completed. Receipt uploaded.",
                    data={"order_id": order.id},
                )

        self.message_user(
            request,
            "Payout marked as completed and sellers notified."
        )

    mark_payout_completed.short_description = (
        "💸 Mark payout completed & notify seller"
    )

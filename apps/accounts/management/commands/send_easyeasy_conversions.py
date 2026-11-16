
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.accounts.models import EasyEasyConversion
from apps.accounts.easyeasy import (
    VENDOR_TYPES,
    send_completion,
)
from apps.products.models import Product


MAX_ATTEMPTS = 5

RETRY_DELAYS = [
    60,
    300,
    1800,
    3600,
    7200,
]


def vendor_has_valid_product(user_id):
    return Product.objects.filter(
        seller_id=user_id
    ).filter(
        Q(images__image__isnull=False) |
        Q(videos__video__isnull=False)
    ).distinct().exists()


class Command(BaseCommand):
    help = "Send qualified vendor completion conversions to EasyEasy."

    def handle(self, *args, **options):
        now = timezone.now()

        conversion_ids = list(
            EasyEasyConversion.objects.filter(
                status__in=["queued", "retry_pending"]
            ).filter(
                Q(next_attempt_at__isnull=True) |
                Q(next_attempt_at__lte=now)
            ).order_by("created_at").values_list(
                "id", flat=True
            )[:50]
        )

        for conversion_id in conversion_ids:
            self.process_conversion(conversion_id)

    def process_conversion(self, conversion_id):
        # Keep the row lock during delivery. This prevents another
        # command instance from sending the same conversion concurrently.
        with transaction.atomic():
            try:
                conversion = (
                    EasyEasyConversion.objects
                    .select_for_update()
                    .select_related("profile", "profile__user")
                    .get(id=conversion_id)
                )
            except EasyEasyConversion.DoesNotExist:
                return

            if conversion.status not in ["queued", "retry_pending"]:
                return

            if (
                conversion.next_attempt_at
                and conversion.next_attempt_at > timezone.now()
            ):
                return

            profile = conversion.profile
            user_id = profile.user_id

            # Recheck the actual current vendor qualification.
            if (
                not profile.verified
                or profile.user_type not in VENDOR_TYPES
                or not profile.easyeasy_subid
                or not vendor_has_valid_product(user_id)
            ):
                conversion.status = "needs_review"
                conversion.next_attempt_at = None
                conversion.last_response = {
                    "reason": (
                        "Vendor no longer meets the qualification "
                        "requirements."
                    )
                }
                conversion.save(update_fields=[
                    "status",
                    "next_attempt_at",
                    "last_response",
                    "updated_at",
                ])
                return

            result = send_completion(
                vendor_id=user_id,
                saved_click_id=conversion.subid,
                vendor_approved=True,
                first_valid_product_uploaded=True,
                order_id=conversion.order_id,
            )

            conversion.attempts += 1
            conversion.last_response = result.get(
                "result",
                {"reason": result.get("reason")}
            )

            conversion.last_http_status = result.get("http_status")

            if result.get("success"):
                conversion.status = "delivered"
                conversion.delivered_at = timezone.now()
                conversion.next_attempt_at = None

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Delivered conversion {conversion.id}"
                    )
                )

            elif result.get("retryable"):
                self.schedule_retry(conversion, result)

            else:
                conversion.status = "needs_review"
                conversion.next_attempt_at = None

                self.stderr.write(
                    f"Conversion {conversion.id} needs review: "
                    f"{result.get('reason', result.get('result'))}"
                )

            conversion.save()

    def schedule_retry(self, conversion, result):
        if conversion.attempts >= MAX_ATTEMPTS:
            conversion.status = "needs_review"
            conversion.next_attempt_at = None
            conversion.last_response = {
                **conversion.last_response,
                "retry_exhausted": True,
            }
            return

        delay_index = min(
            conversion.attempts - 1,
            len(RETRY_DELAYS) - 1
        )

        delay = RETRY_DELAYS[delay_index]

        conversion.status = "retry_pending"
        conversion.next_attempt_at = (
            timezone.now() + timedelta(seconds=delay)
        )

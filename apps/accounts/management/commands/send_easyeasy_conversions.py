import json
import urllib.request
import urllib.error

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import EasyEasyConversion


API_URL = "https://api.easyeasy.ng/api/conversion"


class Command(BaseCommand):

    help = "Send pending EasyEasy signup conversions"

    def handle(self, *args, **options):

        now = timezone.now()

        conversions = EasyEasyConversion.objects.filter(
            status__in=["queued", "retry_pending"]
        ).filter(
            models_q_next_attempt(now)
        ).order_by("created_at")[:50]

        for conversion in conversions:
            self.send_conversion(conversion)

    def send_conversion(self, conversion):

        payload = {
            "subid": conversion.subid,
            "event": "signup",
            "order_id": conversion.order_id,
        }

        request = urllib.request.Request(
            API_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:

            with urllib.request.urlopen(
                request,
                timeout=15
            ) as response:

                http_status = response.status
                raw_response = response.read().decode("utf-8")

        except urllib.error.HTTPError as error:

            http_status = error.code
            raw_response = error.read().decode(
                "utf-8",
                errors="replace"
            )

        except Exception as error:

            self.retry_conversion(
                conversion,
                {"error": str(error)},
                None
            )
            return

        try:
            body = json.loads(raw_response)
        except (ValueError, TypeError):
            body = {"status": "invalid_response"}

        conversion.attempts += 1
        conversion.last_http_status = http_status
        conversion.last_response = body

        if 200 <= http_status < 300 and body.get("status") == "success":

            conversion.status = "delivered"
            conversion.delivered_at = timezone.now()
            conversion.next_attempt_at = None

            self.stdout.write(
                self.style.SUCCESS(
                    f"Delivered: {conversion.order_id}"
                )
            )

        elif body.get("status") == "warning":

            conversion.status = "needs_review"
            conversion.next_attempt_at = None

            self.stdout.write(
                self.style.WARNING(
                    f"Needs review: {conversion.order_id}"
                )
            )

        elif http_status in (429, 500, 502, 503, 504):

            self.retry_conversion(
                conversion,
                body,
                http_status,
                already_counted=True
            )
            return

        else:

            conversion.status = "needs_review"
            conversion.next_attempt_at = None

        conversion.save()

    def retry_conversion(
        self,
        conversion,
        response,
        http_status,
        already_counted=False
    ):

        if not already_counted:
            conversion.attempts += 1

        conversion.last_response = response
        conversion.last_http_status = http_status

        delays = [60, 300, 1800]

        if conversion.attempts <= len(delays):

            conversion.status = "retry_pending"

            conversion.next_attempt_at = (
                timezone.now() +
                timedelta(seconds=delays[conversion.attempts - 1])
            )

        else:

            conversion.status = "needs_review"
            conversion.next_attempt_at = None

        conversion.save()


def models_q_next_attempt(now):
    from django.db.models import Q

    return (
        Q(next_attempt_at__isnull=True) |
        Q(next_attempt_at__lte=now)
    )
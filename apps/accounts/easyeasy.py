
import hashlib
import json
import os
import urllib.error
import urllib.request

from django.db.models import Q

from .models import Profile, EasyEasyConversion
from apps.products.models import Product


VENDOR_TYPES = [
    "tailor",
    "fashion_designer",
    "fashion_brand",
    "fabric_vendor",
]


def check_vendor_conversion(user_id):
    """
    Queue a conversion only when the vendor:
    - Is approved.
    - Has a qualifying vendor account type.
    - Has a saved EasyEasy attribution ID.
    - Has at least one product with an image or video.
    """

    try:
        profile = Profile.objects.get(user_id=user_id)
    except Profile.DoesNotExist:
        return None

    if not profile.verified:
        return None

    if profile.user_type not in VENDOR_TYPES:
        return None

    if not profile.easyeasy_subid:
        return None

    valid_product = Product.objects.filter(
        seller_id=user_id
    ).filter(
        Q(images__image__isnull=False) |
        Q(videos__video__isnull=False)
    ).distinct().exists()

    if not valid_product:
        return None

    conversion, created = EasyEasyConversion.objects.get_or_create(
        profile=profile,
        defaults={
            "subid": profile.easyeasy_subid,
            "order_id": f"vendor:{user_id}:first_valid_product",
            "status": "queued",
        }
    )

    return conversion


def _post(body):
    """
    Send an authenticated request to EasyEasy.
    This function does not modify Imura's database.
    """

    key = os.getenv("EASYEASY_PRIVATE_KEY", "")
    connection = os.getenv("EASYEASY_CONNECTION_ID", "")
    base = os.getenv(
        "EASYEASY_API_BASE",
        "https://api.easyeasy.ng"
    ).rstrip("/")

    if not key or not connection:
        return {
            "success": False,
            "retryable": False,
            "reason": "EasyEasy credentials are not configured."
        }

    payload = {
        **body,
        "connection_id": connection,
        "event": "custom",
        "action": "vendor_product_uploaded",
    }

    request = urllib.request.Request(
        f"{base}/api/conversion",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "X-EasyEasy-Tracking-Key": key,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            raw_response = response.read().decode("utf-8")
            result = json.loads(raw_response)

        return {
            "success": result.get("status") == "success",
            "retryable": False,
            "result": result,
        }

    except urllib.error.HTTPError as error:
        try:
            error_body = error.read().decode("utf-8", errors="replace")
            response_data = json.loads(error_body)
        except (ValueError, TypeError):
            response_data = {"error": "Invalid error response"}

        return {
            "success": False,
            "retryable": error.code == 429 or error.code >= 500,
            "http_status": error.code,
            "result": response_data,
        }

    except (
        urllib.error.URLError,
        TimeoutError,
        OSError,
        ValueError,
    ) as error:
        return {
            "success": False,
            "retryable": True,
            "reason": str(error),
        }


def send_completion(
    vendor_id,
    saved_click_id,
    vendor_approved,
    first_valid_product_uploaded,
    order_id=None,
):
    """
    Send a live qualified-vendor completion event.

    Qualification flags must come from Imura's database,
    never from browser input.
    """

    if vendor_approved is not True:
        return {
            "success": False,
            "retryable": False,
            "reason": "Vendor is not approved."
        }

    if first_valid_product_uploaded is not True:
        return {
            "success": False,
            "retryable": False,
            "reason": "Vendor has no valid product."
        }

    identity = str(vendor_id or "").strip()

    if not identity:
        return {
            "success": False,
            "retryable": False,
            "reason": "Missing vendor ID."
        }

    if (
        not isinstance(saved_click_id, str)
        or not 1 <= len(saved_click_id.strip()) <= 100
    ):
        return {
            "success": False,
            "retryable": False,
            "reason": "Missing or invalid saved attribution ID."
        }

    reference = order_id or (
        f"vendor:{identity}:first_valid_product"
    )

    if len(reference) > 100:
        reference = (
            "vendor:"
            + hashlib.sha256(identity.encode()).hexdigest()
            + ":first_valid_product"
        )

    return _post({
        "is_test": False,
        "subid": saved_click_id.strip(),
        "order_id": reference,
        "vendor_approved": True,
        "first_valid_product_uploaded": True,
    })


def safe_test():
    """
    Test the EasyEasy connection without a real vendor conversion.
    """

    return _post({
        "is_test": True,
    })

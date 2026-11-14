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

    try:
        profile = Profile.objects.get(user_id=user_id)
    except Profile.DoesNotExist:
        return None

    # Only approved vendors qualify.
    if not profile.verified:
        return None

    if profile.user_type not in VENDOR_TYPES:
        return None

    # Referral attribution must exist.
    if not profile.easyeasy_subid:
        return None

    # Vendor must have at least one product with media.
    valid_product = Product.objects.filter(
        seller_id=user_id
    ).filter(
        Q(images__isnull=False) |
        Q(videos__isnull=False)
    ).exists()

    if not valid_product:
        return None

    conversion, created = EasyEasyConversion.objects.get_or_create(
        profile=profile,
        defaults={
            "subid": profile.easyeasy_subid,
            "order_id": f"registration:user-{user_id}",
            "status": "queued",
        }
    )

    return conversion
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction

from .models import ProductImage, ProductVideo


def check_vendor_after_media_upload(product):

    from apps.accounts.easyeasy import check_vendor_conversion

    transaction.on_commit(
        lambda: check_vendor_conversion(product.seller_id)
    )


@receiver(post_save, sender=ProductImage)
def product_image_uploaded(sender, instance, created, **kwargs):

    if created:
        check_vendor_after_media_upload(instance.product)


@receiver(post_save, sender=ProductVideo)
def product_video_uploaded(sender, instance, created, **kwargs):

    if created:
        check_vendor_after_media_upload(instance.product)
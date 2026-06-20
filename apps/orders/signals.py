from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order
from apps.notifications.models import Notification


@receiver(post_save, sender=Order)
def create_order_notification(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            sender=instance.buyer,
            recipient=instance.seller,
            type="info",
            verb=f"check orders page You received a new order for {instance.product.title}",
            data={"order_id": instance.id},
        )
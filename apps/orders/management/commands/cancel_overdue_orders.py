from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.orders.models import Order
from apps.notifications.models import Notification


class Command(BaseCommand):
    help = "Cancel overdue orders that exceeded delivery deadline"

    def handle(self, *args, **kwargs):
        now = timezone.now()

        overdue_orders = Order.objects.filter(
            status__in=["paid", "in_transit"],
            delivery_deadline__lt=now
        )

        if not overdue_orders.exists():
            self.stdout.write(self.style.SUCCESS("No overdue orders found."))
            return

        for order in overdue_orders:
            order.status = "cancelled"
            order.save()

            Notification.objects.create(
                sender=order.seller,
                recipient=order.buyer,
                type="warning",
                verb="Order cancelled due to late delivery",
                data={"order_id": order.id},
            )

            self.stdout.write(
                self.style.WARNING(f"Order {order.id} cancelled due to deadline.")
            )

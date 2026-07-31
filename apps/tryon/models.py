from django.conf import settings
from django.db import models


class TryOnUsage(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tryon_usage",
    )
    tryon_count = models.PositiveIntegerField(default=0)

    MAX_FREE_TRYONS = 2

    def can_use_tryon(self):
        """Returns True if user has remaining try-ons."""
        return self.tryon_count < self.MAX_FREE_TRYONS

    def remaining_tryons(self):
        """Calculates remaining free try-ons available."""
        return max(0, self.MAX_FREE_TRYONS - self.tryon_count)

    def __str__(self):
        return f"{self.user} ({self.tryon_count}/{self.MAX_FREE_TRYONS} try-ons used)"
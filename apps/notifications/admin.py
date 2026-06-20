from django.contrib import admin
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "sender", "recipient", "type", "verb", "read", "accepted", "created_at")
    list_filter = ("type", "read", "accepted", "created_at")
    search_fields = ("sender__username", "recipient__username", "verb")
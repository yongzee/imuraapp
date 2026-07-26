from django.contrib import admin
from .models import Feedback

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    # Columns displayed in the main admin table view
    list_display = ('feedback_type', 'rating_stars', 'name', 'email', 'phone_number', 'short_message', 'created_at')

    # Filters available in the right sidebar
    list_filter = ('feedback_type', 'rating', 'created_at')

    # Search box functionality (searches across name, email, phone, and message)
    search_fields = ('name', 'email', 'phone_number', 'message')

    # Default ordering (newest first)
    ordering = ('-created_at',)

    # Read-only fields so submitted feedback cannot be accidentally edited by staff
    readonly_fields = ('created_at',)

    # Display stars visually in the list view instead of plain numbers
    def rating_stars(self, obj):
        return '★' * obj.rating + '☆' * (5 - obj.rating)
    rating_stars.short_description = 'Rating'

    # Truncate long messages in the table view
    def short_message(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    short_message.short_description = 'Message'
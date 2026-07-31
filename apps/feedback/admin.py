import csv
from django.contrib import admin
from django.http import HttpResponse
from django.utils.html import format_html
from .models import Feedback


@admin.action(description='Export selected feedback to CSV')
def export_as_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="feedback_export.csv"'
    writer = csv.writer(response)
    writer.writerow(['ID', 'Type', 'Rating', 'Name', 'Email', 'Phone', 'Message', 'Submitted At'])
    for obj in queryset:
        writer.writerow([
            obj.id, obj.feedback_type, obj.rating, obj.name,
            obj.email, obj.phone_number, obj.message,
            obj.created_at.strftime('%Y-%m-%d %H:%M:%S') if obj.created_at else ''
        ])
    return response


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    actions = [export_as_csv]

    list_display = (
        'feedback_type', 
        'rating_stars', 
        'name', 
        'email', 
        'phone_number', 
        'short_message', 
        'created_at',
        'view_detail_button',  # Dedicated view button
    )

    list_filter = ('feedback_type', 'rating', 'created_at')
    search_fields = ('name', 'email', 'phone_number', 'message')
    ordering = ('-created_at',)

    # Make multiple columns clickable to open the detail view
    list_display_links = ('name', 'feedback_type', 'short_message')

    fieldsets = (
        ('Submission Info', {
            'fields': ('feedback_type', 'rating_stars_display', 'created_at')
        }),
        ('User Contact Details', {
            'fields': ('name', 'email', 'phone_number')
        }),
        ('Full Feedback Message', {
            'fields': ('full_message_display',),
        }),
    )

    readonly_fields = (
        'feedback_type', 
        'rating', 
        'rating_stars_display', 
        'name', 
        'email', 
        'phone_number', 
        'message', 
        'full_message_display', 
        'created_at'
    )

    # Action button column to open in pop-up window
    @admin.display(description='Action')
    def view_detail_button(self, obj):
        return format_html(
            '<a class="button" href="{}/change/?_popup=1" '
            'onclick="return showAddAnotherPopup(this);" '
            'style="background: #0d6efd; color: white; padding: 3px 10px; border-radius: 4px; text-decoration: none; font-size: 12px;">'
            'View Full</a>',
            obj.id
        )

    @admin.display(description='Rating', ordering='rating')
    def rating_stars(self, obj):
        stars = '★' * obj.rating + '☆' * (5 - obj.rating)
        return format_html('<span style="color: #f39c12; font-size: 14px;">{}</span>', stars)

    @admin.display(description='Rating')
    def rating_stars_display(self, obj):
        stars = '★' * obj.rating + '☆' * (5 - obj.rating)
        return format_html('<span style="color: #f39c12; font-size: 16px; font-weight: bold;">{} ({}/5)</span>', stars, obj.rating)

    @admin.display(description='Message')
    def short_message(self, obj):
        if not obj.message:
            return "-"
        truncated = obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
        return format_html('<span title="{}">{}</span>', obj.message, truncated)

    @admin.display(description='Message')
    def full_message_display(self, obj):
        if not obj.message:
            return "-"
        return format_html(
            '<div style="background-color: #f8f9fa; color: #333; padding: 14px 18px; '
            'border-radius: 6px; border-left: 4px solid #0d6efd; font-size: 14px; '
            'line-height: 1.6; white-space: pre-wrap; word-wrap: break-word;">{}</div>',
            obj.message
        )
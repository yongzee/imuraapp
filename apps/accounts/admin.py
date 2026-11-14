from django.contrib import admin

from .models import (
    Profile,
    UserActivity,
    EasyEasyConversion,
)

from .easyeasy import check_vendor_conversion


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "user_type",
        "business_name",
        "phone",
        "verified",
        "created_at",
    )

    list_filter = (
        "user_type",
        "verified",
        "state",
    )

    search_fields = (
        "user__username",
        "user__email",
        "business_name",
        "phone",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "easyeasy_subid",
    )

    actions = [
        "approve_vendors",
        "reject_vendors",
    ]

    @admin.action(description="Approve selected vendors")
    def approve_vendors(self, request, queryset):

        count = 0

        for profile in queryset:

            if profile.user_type not in [
                "tailor",
                "fashion_designer",
                "fashion_brand",
                "fabric_vendor",
            ]:
                continue

            profile.verified = True
            profile.save(update_fields=["verified", "updated_at"])

            check_vendor_conversion(profile.user_id)
            count += 1

        self.message_user(
            request,
            f"{count} vendor profile(s) approved."
        )

    @admin.action(description="Reject / revoke selected vendors")
    def reject_vendors(self, request, queryset):

        count = queryset.update(verified=False)

        self.message_user(
            request,
            f"{count} profile(s) had approval revoked."
        )


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "action",
        "ip_address",
        "timestamp",
    )

    list_filter = ("action", "timestamp")

    search_fields = (
        "user__username",
        "ip_address",
    )


@admin.register(EasyEasyConversion)
class EasyEasyConversionAdmin(admin.ModelAdmin):

    list_display = (
        "profile",
        "subid",
        "status",
        "attempts",
        "last_http_status",
        "created_at",
    )

    list_filter = ("status",)

    search_fields = (
        "profile__user__username",
        "subid",
        "order_id",
    )

    readonly_fields = (
        "profile",
        "subid",
        "order_id",
        "attempts",
        "last_http_status",
        "last_response",
        "created_at",
        "updated_at",
        "delivered_at",
    )
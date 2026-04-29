from django.contrib import admin
from .models import Campaign, StudentVerification, Coupon, AssignedCoupon


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "coupon_pool_size", "coupons_remaining", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at",)

    def coupon_pool_size(self, obj):
        return obj.coupons.count()
    coupon_pool_size.short_description = "Total codes"

    def coupons_remaining(self, obj):
        return obj.coupons.filter(is_used=False).count()
    coupons_remaining.short_description = "Unused"


@admin.register(StudentVerification)
class StudentVerificationAdmin(admin.ModelAdmin):
    list_display = ("email", "is_verified", "created_at")
    list_filter = ("is_verified",)
    search_fields = ("email",)
    readonly_fields = ("otp", "otp_created_at", "created_at", "updated_at")


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ("code", "campaign", "is_used", "created_at")
    list_filter = ("is_used", "campaign")
    search_fields = ("code",)


@admin.register(AssignedCoupon)
class AssignedCouponAdmin(admin.ModelAdmin):
    list_display = ("student", "campaign", "coupon", "assigned_at", "is_expired_display")
    list_filter = ("campaign",)
    search_fields = ("student__email", "coupon__code")
    readonly_fields = ("assigned_at",)

    def is_expired_display(self, obj):
        return obj.is_expired()
    is_expired_display.boolean = True
    is_expired_display.short_description = "Expired"

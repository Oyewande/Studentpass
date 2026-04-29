from django.db import models
from django.utils import timezone
from datetime import timedelta


class Campaign(models.Model):
    name = models.CharField(max_length=200, help_text="Displayed on the verification page, e.g. 'Caleb Book Sale'")
    slug = models.SlugField(unique=True, help_text="URL identifier, e.g. 'caleb-book-sale' → ?c=caleb-book-sale")
    description = models.TextField(blank=True, help_text="Optional subtitle shown under the campaign name")
    allowed_domains = models.TextField(
        help_text="Comma-separated school email domains allowed for this campaign, e.g. caleb.edu.ng,stu.cu.edu.ng"
    )
    product_url = models.URLField(help_text="Product page URL students are redirected to after getting their code (Selar, Gumroad, Payhip, etc.)")
    is_active = models.BooleanField(default=True, help_text="Inactive campaigns return 404 to the frontend")
    created_at = models.DateTimeField(auto_now_add=True)

    def get_allowed_domains(self) -> list[str]:
        return [d.strip().lower() for d in self.allowed_domains.split(",") if d.strip()]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Campaign"
        verbose_name_plural = "Campaigns"
        ordering = ["-created_at"]


class StudentVerification(models.Model):
    email = models.EmailField(unique=True)
    is_verified = models.BooleanField(default=False)
    otp = models.CharField(max_length=6, blank=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_otp_valid(self) -> bool:
        if not self.otp_created_at:
            return False
        return timezone.now() < self.otp_created_at + timedelta(minutes=10)

    def __str__(self):
        return f"{self.email} ({'verified' if self.is_verified else 'unverified'})"

    class Meta:
        verbose_name = "Student Verification"
        verbose_name_plural = "Student Verifications"


class Coupon(models.Model):
    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.PROTECT,
        related_name="coupons",
        null=True,
        blank=True,
        help_text="Which campaign this code belongs to",
    )
    code = models.CharField(max_length=50, unique=True)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code} ({'used' if self.is_used else 'available'})"

    class Meta:
        verbose_name = "Coupon"
        verbose_name_plural = "Coupons"


class AssignedCoupon(models.Model):
    # Changed from OneToOneField → ForeignKey so one student can hold
    # one coupon per campaign (unique_together enforces the per-campaign limit).
    student = models.ForeignKey(
        StudentVerification,
        on_delete=models.CASCADE,
        related_name="assigned_coupons",
    )
    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.PROTECT,
        related_name="assigned_coupons",
        null=True,
        blank=True,
    )
    coupon = models.OneToOneField(Coupon, on_delete=models.CASCADE)
    lookup_token = models.CharField(max_length=128, blank=True, default="")
    assigned_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at

    def __str__(self):
        status = "expired" if self.is_expired() else "active"
        return f"{self.student.email} → {self.coupon.code} ({status})"

    class Meta:
        verbose_name = "Assigned Coupon"
        verbose_name_plural = "Assigned Coupons"
        # One coupon code per student per campaign
        unique_together = [("student", "campaign")]

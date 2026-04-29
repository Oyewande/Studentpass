"""
Campaign-scoped verification flow:

  Each API request that touches a coupon pool carries a campaign slug.
  Campaigns define their own allowed school domains and Selar product URL,
  so multiple authors can run independent discount campaigns simultaneously.

  A student's identity is their email address — they can hold one coupon
  per campaign, so the same student can redeem codes across different campaigns.

  Email delivery is handled by Django's send_mail() which uses the backend
  configured in settings.py: console in DEBUG mode, Gmail SMTP in production.
"""
import hmac
import logging
import secrets
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response

from .models import StudentVerification, Coupon, AssignedCoupon, Campaign
from .serializers import EmailSerializer, OTPSerializer, CouponLookupSerializer
from .throttles import OTPRequestThrottle, OTPEmailThrottle, OTPVerifyThrottle, CouponLookupThrottle

logger = logging.getLogger(__name__)

COUPON_VALIDITY_HOURS = 24

_NOT_FOUND_MSG = "Invalid or expired code. Please request a new OTP."


def _get_domain(email: str) -> str:
    return email.split("@")[-1].lower()


def _generate_otp() -> str:
    return str(secrets.randbelow(900_000) + 100_000)


def _otp_matches(stored: str, submitted: str) -> bool:
    return hmac.compare_digest(stored.encode(), submitted.encode())


_OTP_BODY = """\
Hi,

Your one-time verification code is:

  {otp}

This code expires in 10 minutes. Do not share it.

— StudentPass Team
"""


def _send_otp_email(to_email: str, otp: str) -> bool:
    try:
        send_mail(
            subject="Your StudentPass Discount OTP",
            message=_OTP_BODY.format(otp=otp),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            fail_silently=False,
        )
        logger.debug("OTP email sent to %s via %s", to_email, settings.EMAIL_BACKEND)
        return True
    except Exception as exc:
        logger.error(
            "OTP email delivery failed for domain %s: %s",
            _get_domain(to_email),
            exc,
            exc_info=True,
        )
        return False


def _get_campaign(slug: str):
    """Returns the Campaign or None if not found / inactive."""
    try:
        return Campaign.objects.get(slug=slug, is_active=True)
    except Campaign.DoesNotExist:
        return None


def _assign_new_coupon(student: StudentVerification, campaign: Campaign) -> tuple[str, str, str]:
    """
    Atomically claim an unused coupon from this campaign's pool.
    Returns (coupon_code, lookup_token, expires_at_iso).
    Raises _CouponPoolEmpty if the pool is exhausted.
    """
    with transaction.atomic():
        coupon = (
            Coupon.objects.select_for_update()
            .filter(is_used=False, campaign=campaign)
            .first()
        )
        if not coupon:
            raise _CouponPoolEmpty()

        coupon.is_used = True
        coupon.save(update_fields=["is_used"])

        lookup_token = secrets.token_urlsafe(32)
        expires_at = timezone.now() + timedelta(hours=COUPON_VALIDITY_HOURS)

        AssignedCoupon.objects.create(
            student=student,
            campaign=campaign,
            coupon=coupon,
            lookup_token=lookup_token,
            expires_at=expires_at,
        )

    return coupon.code, lookup_token, expires_at.isoformat()


class _CouponPoolEmpty(Exception):
    pass


# ── GET /api/campaign/<slug>/ ─────────────────────────────────────────────────
@api_view(["GET"])
def get_campaign_info(request, slug):
    """
    Returns public campaign info so the frontend can show the campaign name,
    validate email domains, and know the Selar redirect URL.
    """
    campaign = _get_campaign(slug)
    if not campaign:
        return Response({"error": "Campaign not found."}, status=404)

    return Response({
        "name": campaign.name,
        "description": campaign.description,
        "allowed_domains": campaign.get_allowed_domains(),
        "product_url": campaign.product_url,
    })


# ── POST /api/request-otp/ ────────────────────────────────────────────────────
@api_view(["POST"])
@throttle_classes([OTPRequestThrottle, OTPEmailThrottle])
def request_otp(request):
    serializer = EmailSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({"error": "Invalid request."}, status=400)

    email = serializer.validated_data["email"]
    campaign_slug = serializer.validated_data["campaign"]

    campaign = _get_campaign(campaign_slug)
    if not campaign:
        return Response({"error": "Campaign not found or no longer active."}, status=404)

    domain = _get_domain(email)
    if domain not in campaign.get_allowed_domains():
        return Response(
            {
                "error": (
                    "This campaign is only available to students from: "
                    f"{', '.join(campaign.get_allowed_domains())}."
                )
            },
            status=400,
        )

    # If the student is already verified AND has an active coupon for THIS campaign,
    # silently return success — no need to re-send an OTP.
    existing = StudentVerification.objects.filter(email=email).first()
    if existing and existing.is_verified:
        try:
            assigned = existing.assigned_coupons.get(campaign=campaign)
            if not assigned.is_expired():
                return Response({"message": "OTP sent to your school email. Check your inbox."})
        except AssignedCoupon.DoesNotExist:
            pass

    otp = _generate_otp()

    StudentVerification.objects.update_or_create(
        email=email,
        defaults={
            "otp": otp,
            "otp_created_at": timezone.now(),
            "is_verified": False,
        },
    )

    sent = _send_otp_email(email, otp)
    if not sent:
        logger.warning(
            "OTP delivery failed for %s (first 2 digits: %s)",
            email,
            otp[:2],
        )

    return Response({"message": "OTP sent to your school email. Check your inbox."})


# ── POST /api/verify-otp/ ─────────────────────────────────────────────────────
@api_view(["POST"])
@throttle_classes([OTPVerifyThrottle])
def verify_otp(request):
    serializer = OTPSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({"error": "Invalid request."}, status=400)

    email = serializer.validated_data["email"]
    otp = serializer.validated_data["otp"]
    campaign_slug = serializer.validated_data["campaign"]

    campaign = _get_campaign(campaign_slug)
    if not campaign:
        return Response({"error": "Campaign not found or no longer active."}, status=404)

    try:
        student = StudentVerification.objects.get(email=email)
    except StudentVerification.DoesNotExist:
        return Response({"error": _NOT_FOUND_MSG}, status=400)

    if not _otp_matches(student.otp, otp):
        return Response({"error": _NOT_FOUND_MSG}, status=400)

    if not student.is_otp_valid():
        return Response({"error": _NOT_FOUND_MSG}, status=400)

    student.is_verified = True
    student.save(update_fields=["is_verified"])

    coupon_code = lookup_token = expires_at_iso = None

    try:
        assigned = student.assigned_coupons.get(campaign=campaign)
        if assigned.is_expired():
            assigned.delete()
            raise AssignedCoupon.DoesNotExist
        coupon_code = assigned.coupon.code
        lookup_token = assigned.lookup_token
        expires_at_iso = assigned.expires_at.isoformat() if assigned.expires_at else None

    except AssignedCoupon.DoesNotExist:
        try:
            coupon_code, lookup_token, expires_at_iso = _assign_new_coupon(student, campaign)
        except _CouponPoolEmpty:
            return Response(
                {"error": "All discount codes have been claimed. Check back soon!"},
                status=503,
            )

    return Response({
        "message": "Verified! Here's your exclusive discount code.",
        "coupon": coupon_code,
        "lookup_token": lookup_token,
        "expires_at": expires_at_iso,
    })


# ── GET /api/get-coupon/?email=...&token=... ──────────────────────────────────
@api_view(["GET"])
@throttle_classes([CouponLookupThrottle])
def get_coupon(request):
    """
    No campaign needed here — the lookup_token is unique per AssignedCoupon
    and already identifies the specific campaign assignment.
    """
    serializer = CouponLookupSerializer(data=request.GET)
    if not serializer.is_valid():
        return Response({"error": "Email and token are required."}, status=400)

    email = serializer.validated_data["email"]
    token = serializer.validated_data["token"]

    try:
        student = StudentVerification.objects.get(email=email, is_verified=True)
        assigned = student.assigned_coupons.get(lookup_token=token)
    except (StudentVerification.DoesNotExist, AssignedCoupon.DoesNotExist):
        return Response({"error": "Not found."}, status=404)

    if not hmac.compare_digest(assigned.lookup_token.encode(), token.encode()):
        return Response({"error": "Not found."}, status=404)

    if assigned.is_expired():
        return Response(
            {"error": "This discount code has expired. Please re-verify to get a new one."},
            status=410,
        )

    return Response({
        "coupon": assigned.coupon.code,
        "expires_at": assigned.expires_at.isoformat() if assigned.expires_at else None,
    })

"""
Custom DRF throttle classes for OTP endpoints.

/request-otp/ is protected by TWO independent throttles:
  • OTPRequestThrottle — 3 requests per hour per IP address
  • OTPEmailThrottle   — 3 requests per hour per email address

Both must pass for the request to proceed. This prevents:
  - IP rotation attacks (email throttle still blocks them)
  - Email enumeration at scale (IP throttle blocks bulk scanning)

Rates are configurable via settings.py REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"].
"""
from rest_framework.throttling import AnonRateThrottle, SimpleRateThrottle


class OTPRequestThrottle(AnonRateThrottle):
    """3 OTP requests per hour per IP address."""
    scope = "otp_request"


class OTPEmailThrottle(SimpleRateThrottle):
    """
    3 OTP requests per hour per email address.

    Uses the email from the POST body as the cache key so that an attacker
    rotating IP addresses still cannot spam OTPs to a single target address.
    """
    scope = "otp_email"

    def get_cache_key(self, request, view):
        email = request.data.get("email", "").lower().strip()
        if not email:
            # No email in body — let the IP throttle handle it; skip this one.
            return None
        return self.cache_format % {
            "scope": self.scope,
            "ident": email,
        }


class OTPVerifyThrottle(AnonRateThrottle):
    """
    10 verify attempts per hour per IP.
    With a 6-digit OTP (900 000 possibilities) and 10 attempts/hour,
    brute-forcing the correct code takes ~10 250 hours on average.
    """
    scope = "otp_verify"


class CouponLookupThrottle(AnonRateThrottle):
    """3 coupon lookups per hour per IP."""
    scope = "coupon_lookup"

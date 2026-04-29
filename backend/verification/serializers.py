import re
from rest_framework import serializers


class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField()
    campaign = serializers.SlugField()

    def validate_email(self, value: str) -> str:
        return value.lower().strip()


class OTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(min_length=6, max_length=6)
    campaign = serializers.SlugField()

    def validate_email(self, value: str) -> str:
        return value.lower().strip()

    def validate_otp(self, value: str) -> str:
        if not value.isdigit():
            raise serializers.ValidationError("OTP must be 6 digits.")
        return value


class CouponLookupSerializer(serializers.Serializer):
    """
    Requires both email and the secret lookup_token issued at verification time.
    """
    email = serializers.EmailField()
    token = serializers.CharField(min_length=10, max_length=128)

    def validate_email(self, value: str) -> str:
        return value.lower().strip()

    def validate_token(self, value: str) -> str:
        if not re.match(r'^[A-Za-z0-9_\-]+$', value):
            raise serializers.ValidationError("Invalid token format.")
        return value

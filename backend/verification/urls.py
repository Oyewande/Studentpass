from django.urls import path
from .views import request_otp, verify_otp, get_coupon, get_campaign_info

urlpatterns = [
    path("campaign/<slug:slug>/", get_campaign_info, name="campaign-info"),
    path("request-otp/", request_otp, name="request-otp"),
    path("verify-otp/", verify_otp, name="verify-otp"),
    path("get-coupon/", get_coupon, name="get-coupon"),
]

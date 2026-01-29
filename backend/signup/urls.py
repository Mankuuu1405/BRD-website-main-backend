from django.urls import path
from .views import send_otp, verify_otp, resend_otp

urlpatterns = [
    path("send-otp/", send_otp, name="send-otp"),
    path("verify-otp/", verify_otp, name="verify-otp"),
    path("resend-otp/", resend_otp, name="resend-otp"),
]

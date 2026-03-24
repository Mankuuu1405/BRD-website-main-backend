from django.urls import path
from .views import send_otp, verify_otp, resend_otp, register_user, login_user

urlpatterns = [
    path("send-otp/", send_otp),
    path("verify-otp/", verify_otp),
    path("resend-otp/", resend_otp),
    path("register/", register_user),  
    path("login/", login_user),        
]
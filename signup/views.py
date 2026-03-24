from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from .models import Business, PendingRegistration

import requests
import random

User = get_user_model()

# ---------------------------
# Helper: Send SMS via Twilio
# ---------------------------
def send_sms(phone_number, otp):
    try:
        account_sid = settings.TWILIO_ACCOUNT_SID
        auth_token  = settings.TWILIO_AUTH_TOKEN
        from_whatsapp = f"whatsapp:{settings.TWILIO_WHATSAPP_FROM}"

        formatted = phone_number if phone_number.startswith('+') else f"+91{phone_number}"
        to_whatsapp = f"whatsapp:{formatted}"

        response = requests.post(
            f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json",
            auth=(account_sid, auth_token),
            data={
                "From": from_whatsapp,
                "To": to_whatsapp,
                "Body": f"Your OTP is {otp}. Valid for 5 minutes."
            }
        )

        print("Twilio:", response.status_code, response.text)
        return response.status_code == 201

    except Exception as e:
        print("SMS ERROR:", str(e))
        return False


# ---------------------------
# Generate OTP
# ---------------------------
def generate_otp(mobile_no):
    otp = str(random.randint(100000, 999999))
    cache.set(f"otp_{mobile_no}", otp, timeout=300)
    return otp


# ---------------------------
# SEND OTP
# ---------------------------
@api_view(["POST"])
def send_otp(request):
    mobile_no = request.data.get("mobile_no")
    email     = request.data.get("email")

    if not mobile_no or not email:
        return Response({"error": "Mobile & email required"}, status=400)

    if User.objects.filter(mobile_no=mobile_no).exists():
        return Response({"error": "Mobile already registered"}, status=400)

    if User.objects.filter(email=email).exists():
        return Response({"error": "Email already registered"}, status=400)

    try:
        PendingRegistration.objects.update_or_create(
            mobile_no=mobile_no,
            defaults={
                "email": email,
                "registration_data": request.data
            }
        )

        otp = generate_otp(mobile_no)

        if send_sms(mobile_no, otp):
            return Response({
                "status": "pending",
                "message": "OTP sent"
            })

        return Response({"error": "OTP sending failed"}, status=500)

    except Exception as e:
        return Response({"error": str(e)}, status=500)


# ---------------------------
# VERIFY OTP + CREATE USER
# ---------------------------
@api_view(["POST"])
def verify_otp(request):
    mobile_no = request.data.get("mobile_no")
    otp       = request.data.get("otp")

    if not mobile_no or not otp:
        return Response({"error": "Mobile & OTP required"}, status=400)

    try:
        pending = PendingRegistration.objects.filter(mobile_no=mobile_no).first()

        if not pending:
            return Response({"error": "No pending registration"}, status=404)

        saved_otp = cache.get(f"otp_{mobile_no}")

        if not saved_otp:
            return Response({"error": "OTP expired"}, status=400)

        if saved_otp != otp:
            return Response({"error": "Invalid OTP"}, status=400)

        data = pending.registration_data

        with transaction.atomic():
            user = User.objects.create_user(
                email=data.get("email"),
                mobile_no=data.get("mobile_no"),
                password=data.get("password"),   # ✅ FIXED
                contact_person=data.get("contact_person"),
                is_mobile_verified=True
            )

            Business.objects.create(
                user=user,
                business_name=data.get("business_name"),
                business_type=data.get("business_type"),
                business_pan=data.get("business_pan", ""),
                owner_pan=data.get("owner_pan", ""),
                gst_number=data.get("gst_number", ""),
                loan_product=data.get("loan_product", []),
                address_line1=data.get("address_line1"),
                address_line2=data.get("address_line2", ""),
                city=data.get("city"),
                state=data.get("state"),
                pincode=data.get("pincode"),
                country=data.get("country"),
                status=data.get("status", "Active"),
            )

        cache.delete(f"otp_{mobile_no}")
        pending.delete()

        return Response({
            "message": "Registration successful"
        })

    except Exception as e:
        return Response({"error": str(e)}, status=500)


# ---------------------------
# DIRECT REGISTER (NO OTP)
# ---------------------------
@api_view(["POST"])
def register_user(request):
    try:
        data = request.data
        print("REGISTER DATA:", data)

        import json

        email = data.get("email")
        mobile_no = data.get("mobile_no")

        # ✅ Validate required fields
        if not email:
            return Response({"error": "Email is required"}, status=400)

        if not mobile_no:
            return Response({"error": "Mobile number is required"}, status=400)

        if not data.get("password"):
            return Response({"error": "Password is required"}, status=400)

        # ✅ Duplicate checks
        if User.objects.filter(email=email).exists():
            return Response({"error": "Email already registered"}, status=400)

        if User.objects.filter(mobile_no=mobile_no).exists():
            return Response({"error": "Mobile number already registered"}, status=400)

        # ✅ Fix mapping
        business_type = data.get("business_type") or data.get("organisation_type") or "General"

        with transaction.atomic():
            user = User.objects.create_user(
                email=email,
                mobile_no=mobile_no,
                password=data.get("password"),
                contact_person=data.get("contact_person") or "User",
                is_mobile_verified=True
            )

            Business.objects.create(
                user=user,
                business_name=data.get("business_name") or "Default Business",
                business_type=business_type,

                business_pan=data.get("business_pan", ""),
                owner_pan=data.get("owner_pan", ""),
                gst_number=data.get("gst_number", ""),

                business_description=data.get("business_description", "N/A"),
                subscription_type=data.get("subscription_type", "Free"),

                loan_product=json.dumps(data.get("loan_product", [])),

                address_line1=data.get("address_line1") or "N/A",
                address_line2=data.get("address_line2", ""),
                city=data.get("city") or "N/A",
                state=data.get("state") or "N/A",
                pincode=data.get("pincode") or "000000",
                country=data.get("country") or "India",

                status=data.get("status", "Active"),
            )

        return Response({"message": "Registration successful"}, status=201)

    except Exception as e:
        import traceback
        print("🔥 REGISTER ERROR:", str(e))
        traceback.print_exc()
        return Response({"error": str(e)}, status=400)
# ---------------------------
# LOGIN
# ---------------------------
@api_view(["POST"])
def login_user(request):
    try:
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response({"error": "Email & password required"}, status=400)

        user = User.objects.filter(email=email).first()

        if not user:
            return Response({"error": "User not found"}, status=404)

        if not check_password(password, user.password):
            return Response({"error": "Invalid credentials"}, status=401)

        return Response({
            "message": "Login successful",
            "user_id": user.id,
            "email": user.email
        })

    except Exception as e:
        print("LOGIN ERROR:", str(e))
        return Response({"error": str(e)}, status=500)


# ---------------------------
# RESEND OTP
# ---------------------------
@api_view(["POST"])
def resend_otp(request):
    mobile_no = request.data.get("mobile_no")

    if not mobile_no:
        return Response({"error": "Mobile required"}, status=400)

    pending = PendingRegistration.objects.filter(mobile_no=mobile_no).first()

    if not pending:
        return Response({"error": "No pending registration"}, status=404)

    otp = generate_otp(mobile_no)

    if send_sms(mobile_no, otp):
        return Response({"message": "OTP resent"})

    return Response({"error": "Failed to resend OTP"}, status=500)
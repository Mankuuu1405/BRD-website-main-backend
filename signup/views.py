from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from twilio.rest import Client
from django.conf import settings
from .models import User, Business, PendingRegistration
from django.db import transaction
import random
import string

# Initialize Twilio client
client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
VERIFY_SID = settings.TWILIO_VERIFY_SERVICE_SID

# ---------------------------
# Send OTP to Mobile
# ---------------------------
@api_view(["POST"])
def send_otp(request):
    """
    Stores registration data temporarily and sends OTP via Twilio
    """
    mobile_no = request.data.get("mobile_no")
    email = request.data.get("email")

    if not mobile_no:
        return Response({"error": "Mobile number is required"}, status=400)

    # Check if user already exists
    if User.objects.filter(mobile_no=mobile_no).exists():
        return Response({"error": "Mobile number already registered"}, status=400)
    
    if User.objects.filter(email=email).exists():
        return Response({"error": "Email already registered"}, status=400)

    try:
        # Store the entire registration data temporarily
        PendingRegistration.objects.update_or_create(
            mobile_no=mobile_no,
            defaults={
                "email": email,
                "registration_data": request.data
            }
        )

        # Format mobile number for Twilio (assuming Indian number)
        # Adjust country code based on your requirements
        formatted_mobile = mobile_no
        if not formatted_mobile.startswith('+'):
            # Add country code if not present (e.g., +91 for India)
            formatted_mobile = f"+91{mobile_no}"

        # Send OTP via Twilio Verify
        verification = client.verify.v2.services(VERIFY_SID).verifications.create(
            to=formatted_mobile,
            channel="sms"
        )

        return Response({
            "status": verification.status,
            "message": f"OTP sent to {mobile_no}",
            "mobile_no": mobile_no
        })

    except Exception as e:
        return Response({"error": str(e)}, status=500)

# ---------------------------
# Verify OTP and Complete Registration
# ---------------------------
@api_view(["POST"])
def verify_otp(request):
    """
    Verifies OTP and completes user registration
    """
    mobile_no = request.data.get("mobile_no")
    code = request.data.get("otp")

    if not mobile_no or not code:
        return Response({"error": "Mobile number and OTP are required"}, status=400)

    try:
        # Get pending registration data
        pending_reg = PendingRegistration.objects.filter(mobile_no=mobile_no).first()
        
        if not pending_reg:
            return Response({"error": "No pending registration found for this mobile number"}, status=404)
        
        if pending_reg.is_expired():
            pending_reg.delete()
            return Response({"error": "Registration session expired. Please start again."}, status=400)

        # Format mobile number for Twilio verification
        formatted_mobile = mobile_no
        if not formatted_mobile.startswith('+'):
            formatted_mobile = f"+91{mobile_no}"

        # Verify OTP with Twilio
        verification_check = client.verify.v2.services(VERIFY_SID).verification_checks.create(
            to=formatted_mobile,
            code=code
        )

        if verification_check.status == "approved":
            # OTP verified successfully - create user and business
            registration_data = pending_reg.registration_data
            
            with transaction.atomic():
                # Generate temporary password
                temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
                
                # Create User
                user = User.objects.create_user(
                    email=registration_data['email'],
                    mobile_no=registration_data['mobile_no'],
                    password=temp_password,
                    contact_person=registration_data['contact_person'],
                    is_mobile_verified=True
                )
                
                # Create Business
                Business.objects.create(
                    user=user,
                    business_name=registration_data['business_name'],
                    business_type=registration_data['business_type'],
                    business_pan=registration_data.get('business_pan', ''),
                    owner_pan=registration_data.get('owner_pan', ''),
                    gst_number=registration_data.get('gst_number', ''),
                    duns_number=registration_data.get('duns_number', ''),
                    cin=registration_data.get('cin', ''),
                    business_website=registration_data.get('business_website', ''),
                    business_description=registration_data['business_description'],
                    subscription_type=registration_data['subscription_type'],
                    loan_product=registration_data.get('loan_product', []),
                    address_line1=registration_data['address_line1'],
                    address_line2=registration_data.get('address_line2', ''),
                    city=registration_data['city'],
                    state=registration_data['state'],
                    pincode=registration_data['pincode'],
                    country=registration_data['country'],
                    status=registration_data.get('status', 'Active')
                )
                
                # Delete pending registration
                pending_reg.delete()
                
                # TODO: Send email with temporary password
                # You can integrate email service here
                print(f"Temporary password for {user.email}: {temp_password}")
                
                return Response({
                    "verified": True,
                    "message": "Registration successful! Temporary password sent to your email.",
                    "email": user.email
                })
        else:
            return Response({
                "verified": False,
                "error": "Invalid or expired OTP"
            }, status=400)

    except PendingRegistration.DoesNotExist:
        return Response({"error": "No pending registration found"}, status=404)
    except Exception as e:
        return Response({"error": str(e)}, status=500)

# ---------------------------
# Resend OTP
# ---------------------------
@api_view(["POST"])
def resend_otp(request):
    """
    Resends OTP to the mobile number
    """
    mobile_no = request.data.get("mobile_no")
    
    if not mobile_no:
        return Response({"error": "Mobile number is required"}, status=400)
    
    # Check if pending registration exists
    pending_reg = PendingRegistration.objects.filter(mobile_no=mobile_no).first()
    
    if not pending_reg:
        return Response({"error": "No pending registration found"}, status=404)
    
    try:
        formatted_mobile = mobile_no
        if not formatted_mobile.startswith('+'):
            formatted_mobile = f"+91{mobile_no}"
        
        verification = client.verify.v2.services(VERIFY_SID).verifications.create(
            to=formatted_mobile,
            channel="sms"
        )
        
        return Response({
            "status": verification.status,
            "message": f"OTP resent to {mobile_no}"
        })
    
    except Exception as e:
        return Response({"error": str(e)}, status=500)


from rest_framework import serializers
from .models import User, Business, BUSINESS_TYPES, SUBSCRIPTION_TYPES, LOAN_PRODUCT_CHOICES

# ----------------------------
# User Serializer
# ----------------------------
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "mobile_no", "contact_person"]


# ----------------------------
# Business Serializer
# ----------------------------
class BusinessSerializer(serializers.ModelSerializer):
    class Meta:
        model = Business
        exclude = ["user"]  # Exclude the related user field


# ----------------------------
# Registration Serializer
# ----------------------------
class RegisterSerializer(serializers.Serializer):
    # User fields
    email = serializers.EmailField()
    mobile_no = serializers.CharField()
    contact_person = serializers.CharField()

    # Business fields
    business_name = serializers.CharField()
    business_type = serializers.ChoiceField(choices=BUSINESS_TYPES)
    subscription_type = serializers.ChoiceField(choices=SUBSCRIPTION_TYPES)
    loan_product = serializers.ChoiceField(choices=LOAN_PRODUCT_CHOICES)

    # Optional business identifiers
    business_pan = serializers.CharField(required=False, allow_blank=True)
    owner_pan = serializers.CharField(required=False, allow_blank=True)
    gst_number = serializers.CharField(required=False, allow_blank=True)
    duns_number = serializers.CharField(required=False, allow_blank=True)
    cin = serializers.CharField(required=False, allow_blank=True)

    # Optional website
    business_website = serializers.URLField(required=False, allow_blank=True)

    # Description
    business_description = serializers.CharField()

    # Address fields
    address_line1 = serializers.CharField()
    address_line2 = serializers.CharField(required=False, allow_blank=True)
    city = serializers.CharField()
    state = serializers.CharField()
    pincode = serializers.CharField()
    country = serializers.CharField()

class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    mobile_no = serializers.CharField()
    otp = serializers.CharField()

class SendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    mobile_no = serializers.CharField()
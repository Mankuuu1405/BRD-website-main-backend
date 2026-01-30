from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import RegexValidator, URLValidator
from django.core.exceptions import ValidationError
import uuid
from datetime import timedelta
from django.utils import timezone

# ---------------------------
# Constants
# ---------------------------
LOAN_PRODUCT_CHOICES = [
    ("Working Capital", "Working Capital"),
    ("Equipment Financing", "Equipment Financing"),
    ("Line of Credit", "Line of Credit"),
    ("Merchant Cash Advance", "Merchant Cash Advance"),
]

BUSINESS_TYPES = [
    ("Private Limited", "Private Limited"),
    ("LLP", "LLP"),
    ("Proprietorship", "Proprietorship"),
]

SUBSCRIPTION_TYPES = [
    ("Trial", "Trial"),
    ("Paid", "Paid"),
]

# ---------------------------
# Custom User Manager
# ---------------------------
class CustomUserManager(BaseUserManager):
    def create_user(self, email, mobile_no, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        if not mobile_no:
            raise ValueError("Mobile number is required")

        email = self.normalize_email(email)
        user = self.model(email=email, mobile_no=mobile_no, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, mobile_no, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if not extra_fields.get("is_staff"):
            raise ValueError("Superuser must have is_staff=True")
        if not extra_fields.get("is_superuser"):
            raise ValueError("Superuser must have is_superuser=True")

        return self.create_user(email, mobile_no, password, **extra_fields)

# ---------------------------
# Custom User Model
# ---------------------------
class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    mobile_no = models.CharField(
        max_length=15,
        unique=True,
        validators=[RegexValidator(r'^\+?\d{10,15}$', message="Enter a valid mobile number.")]
    )
    contact_person = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    # Avoid clashes with default auth fields
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_set_permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    # OTP verification status
    is_mobile_verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["mobile_no"]

    objects = CustomUserManager()

    def __str__(self):
        return self.email

# ---------------------------
# Business Model
# ---------------------------
class Business(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="business")
    business_name = models.CharField(max_length=200)
    business_type = models.CharField(max_length=50, choices=BUSINESS_TYPES)
    business_pan = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        validators=[RegexValidator(r'^[A-Z]{5}\d{4}[A-Z]$', message="Enter a valid PAN.")]
    )
    owner_pan = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        validators=[RegexValidator(r'^[A-Z]{5}\d{4}[A-Z]$', message="Enter a valid PAN.")]
    )
    gst_number = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        validators=[RegexValidator(r'^\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}[Z]{1}[A-Z\d]{1}$', message="Enter a valid GSTIN.")]
    )
    duns_number = models.CharField(
        max_length=9,
        blank=True,
        null=True,
        validators=[RegexValidator(r'^\d{9}$', message="Enter a valid DUNS number.")]
    )
    cin = models.CharField(
        max_length=21,
        blank=True,
        null=True,
        validators=[RegexValidator(r'^[A-Z]{1}\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6}$', message="Enter a valid CIN.")]
    )
    business_website = models.URLField(blank=True, null=True, validators=[URLValidator()])
    business_description = models.TextField()
    subscription_type = models.CharField(max_length=10, choices=SUBSCRIPTION_TYPES)
    loan_product = models.JSONField(default=list)  # Store array of selected loan products

    # Address
    address_line1 = models.CharField(max_length=200)
    address_line2 = models.CharField(max_length=200, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    country = models.CharField(max_length=100)
    
    status = models.CharField(max_length=20, default="Active")

    def __str__(self):
        return self.business_name

# ---------------------------
# Pending Registration Model
# ---------------------------
class PendingRegistration(models.Model):
    """Stores registration data before OTP verification"""
    mobile_no = models.CharField(max_length=15, unique=True)
    email = models.EmailField()
    registration_data = models.JSONField()  # Stores entire form data
    created_at = models.DateTimeField(auto_now_add=True)
    
    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=30)
    
    def __str__(self):
        return f"Pending: {self.email}"


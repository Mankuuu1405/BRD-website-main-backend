from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django import forms
from django.core.exceptions import ValidationError
from .models import User, Business

# -------------------------------
# User creation & change forms
# -------------------------------
class UserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirm Password", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ("email", "mobile_no", "contact_person")

    def clean_password2(self):
        pw1 = self.cleaned_data.get("password1")
        pw2 = self.cleaned_data.get("password2")
        if pw1 and pw2 and pw1 != pw2:
            raise ValidationError("Passwords do not match")
        return pw2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    class Meta:
        model = User
        fields = "__all__"


# -------------------------------
# User Admin
# -------------------------------
class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    model = User

    list_display = (
        "email",
        "mobile_no",
        "contact_person",
        "is_email_verified",
        "is_mobile_verified",
        "is_staff",
        "is_active",
        "created_at",
    )
    list_filter = ("is_staff", "is_active", "is_email_verified", "is_mobile_verified")
    search_fields = ("email", "mobile_no", "contact_person")
    ordering = ("email",)

    readonly_fields = ("created_at", "updated_at", "email_otp", "mobile_otp")

    fieldsets = (
        (None, {"fields": ("email", "mobile_no", "contact_person", "password")}),
        ("Verification", {"fields": ("email_otp", "mobile_otp", "is_email_verified", "is_mobile_verified")}),
        ("Permissions", {"fields": ("is_staff", "is_active", "is_superuser", "groups", "user_permissions")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "mobile_no", "contact_person", "password1", "password2", "is_staff", "is_active"),
        }),
    )


# -------------------------------
# Inline for Business inside User
# -------------------------------
class BusinessInline(admin.StackedInline):
    model = Business
    can_delete = False
    verbose_name_plural = "Business"
    fk_name = "user"
    fields = (
        "business_name",
        "business_type",
        "subscription_type",
        "loan_product",
        "status",
        "business_pan",
        "owner_pan",
        "gst_number",
        "duns_number",
        "cin",
        "business_website",
        "business_description",
        "address_line1",
        "address_line2",
        "city",
        "state",
        "pincode",
        "country",
    )
    readonly_fields = ("status",)


# Attach inline to UserAdmin
UserAdmin.inlines = [BusinessInline]


# -------------------------------
# Business Admin
# -------------------------------
@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = (
        "business_name",
        "business_type",
        "subscription_type",
        "loan_product",
        "status",
        "city",
        "state",
        "country",
    )
    list_filter = ("business_type", "loan_product","subscription_type", "status", "state", "country")
    search_fields = ("business_name", "city", "state", "country")
    ordering = ("business_name",)
    readonly_fields = ("status",)
    exclude = ("user",)

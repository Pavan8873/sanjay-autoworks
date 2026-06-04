from django import forms
from django.core.exceptions import ValidationError
import re
from .models import Customer, Vehicle


class UppercaseMixin:
    def clean(self):
        cleaned = super().clean()
        for key, value in cleaned.items():
            if isinstance(value, str):
                cleaned[key] = value.upper().strip()
        return cleaned


def _validate_alpha_name(value, label="Name"):
    text = (value or "").strip().upper()
    if not text:
        raise ValidationError(f"{label} is required.")
    if not re.fullmatch(r"[A-Z ]+", text):
        raise ValidationError(f"{label} should contain only alphabets and spaces.")
    return text


def _validate_digits(value, min_len=1, label="Number"):
    stripped = re.sub(r"[\s\+\-\(\)]+", "", (value or ""))
    digits = "".join(ch for ch in stripped if ch.isdigit())
    if len(digits) < min_len:
        raise ValidationError(f"{label} must have at least {min_len} digits.")
    if not stripped.isdigit():
        raise ValidationError(f"{label} should contain only numbers (spaces, +, - are allowed).")
    return digits


class CustomerForm(UppercaseMixin, forms.ModelForm):
    class Meta:
        model = Customer
        fields = ["name", "phone", "email", "address", "gstin"]

    def clean(self):
        # Preserve original email before UppercaseMixin converts it
        original_email = (self.data.get("email") or "").strip() if self.data else ""
        
        cleaned = super().clean()
        # Restore original email as entered by user
        cleaned['email'] = original_email
        return cleaned

    def clean_name(self):
        return _validate_alpha_name(self.cleaned_data.get("name"), "Customer name")

    def clean_phone(self):
        return _validate_digits(self.cleaned_data.get("phone"), min_len=10, label="Phone")


class VehicleForm(UppercaseMixin, forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = [
            "vehicle_type", "registration_number", "make", "model", "color", "year",
            "engine_number", "chassis_number", "odometer",
            "insurance_expiry", "pollution_expiry", "rc_expiry",
        ]
        widgets = {
            "insurance_expiry": forms.DateInput(attrs={"type": "date"}),
            "pollution_expiry": forms.DateInput(attrs={"type": "date"}),
            "rc_expiry": forms.DateInput(attrs={"type": "date"}),
        }

    def clean(self):
        # Don't uppercase vehicle_type - keep it lowercase as per model choices
        cleaned = super().clean()
        if 'vehicle_type' in cleaned and isinstance(cleaned['vehicle_type'], str):
            cleaned['vehicle_type'] = cleaned['vehicle_type'].lower()
        return cleaned

    def clean_registration_number(self):
        reg = (self.cleaned_data.get("registration_number") or "").strip().upper()
        reg = re.sub(r"\s+", " ", reg)
        if not re.fullmatch(r"[A-Z0-9 \-]+", reg):
            raise ValidationError("Vehicle number can contain only letters, numbers, space and '-'.")
        if not (any(ch.isalpha() for ch in reg) and any(ch.isdigit() for ch in reg)):
            raise ValidationError("Vehicle number must contain both letters and numbers.")
        return reg


class QuickRegisterForm(UppercaseMixin, forms.Form):
    name = forms.CharField(max_length=200)
    phone = forms.CharField(max_length=20)
    email = forms.EmailField(required=False)
    address = forms.CharField(widget=forms.Textarea(attrs={"rows": 2}), required=False)
    gstin = forms.CharField(max_length=20, required=False, label="GSTIN (optional)")

    vehicle_type = forms.ChoiceField(choices=Vehicle.VEHICLE_TYPES, initial="car")
    registration_number = forms.CharField(max_length=20)
    make = forms.CharField(max_length=80)
    model = forms.CharField(max_length=80)
    engine_number = forms.CharField(max_length=60, required=False)
    chassis_number = forms.CharField(max_length=60, required=False)
    color = forms.CharField(max_length=40, required=False)
    year = forms.IntegerField(required=False)
    odometer = forms.IntegerField(required=False, initial=0)
    inspection_notes = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), required=False, label="Inspection Notes / Issues")

    def clean(self):
        # Preserve original email before UppercaseMixin converts it
        original_email = (self.data.get("email") or "").strip() if self.data else ""
        
        # Don't uppercase vehicle_type - keep it lowercase as per model choices
        # Don't uppercase email - keep it as entered by user
        cleaned = super().clean()
        if 'vehicle_type' in cleaned and isinstance(cleaned['vehicle_type'], str):
            cleaned['vehicle_type'] = cleaned['vehicle_type'].lower()
        # Restore original email as entered by user
        cleaned['email'] = original_email
        return cleaned

    def clean_name(self):
        return _validate_alpha_name(self.cleaned_data.get("name"), "Customer name")

    def clean_phone(self):
        return _validate_digits(self.cleaned_data.get("phone"), min_len=10, label="Phone")

    def clean_registration_number(self):
        reg = (self.cleaned_data.get("registration_number") or "").strip().upper()
        if not re.fullmatch(r"[A-Z0-9 -]+", reg):
            raise ValidationError("Vehicle number can contain only letters, numbers, space and '-'.")
        if not (any(ch.isalpha() for ch in reg) and any(ch.isdigit() for ch in reg)):
            raise ValidationError("Vehicle number must contain both letters and numbers.")
        return reg

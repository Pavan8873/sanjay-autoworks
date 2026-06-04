from django import forms
from django.core.exceptions import ValidationError
import re
from .models import Part, Supplier, StockMovement


class UppercaseMixin:
    def clean(self):
        cleaned = super().clean()
        for key, value in cleaned.items():
            if isinstance(value, str):
                cleaned[key] = value.upper().strip()
        return cleaned


class PartForm(UppercaseMixin, forms.ModelForm):
    class Meta:
        model = Part
        fields = ["sku", "name", "description", "category", "supplier", "unit_price", "stock", "reorder_level"]

    def clean_sku(self):
        sku = (self.cleaned_data.get("sku") or "").strip().upper()
        if not re.fullmatch(r"[A-Z0-9-]+", sku):
            raise ValidationError("SKU can contain only uppercase letters, numbers and '-'.")
        return sku


class SupplierForm(UppercaseMixin, forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ["name", "phone", "email", "address"]

    def clean(self):
        # Preserve original email before UppercaseMixin converts it
        original_email = (self.data.get("email") or "").strip() if self.data else ""
        
        cleaned = super().clean()
        # Restore original email as entered by user
        cleaned['email'] = original_email
        return cleaned

    def clean_name(self):
        name = (self.cleaned_data.get("name") or "").strip()
        if not re.fullmatch(r"[A-Z ]+", name):
            raise ValidationError("Supplier name should contain only alphabets and spaces.")
        return name

    def clean_phone(self):
        phone = (self.cleaned_data.get("phone") or "").strip()
        if phone and (not phone.isdigit() or len(phone) < 10):
            raise ValidationError("Supplier phone should contain only numbers (at least 10 digits).")
        return phone


class RestockForm(UppercaseMixin, forms.Form):
    quantity = forms.IntegerField(min_value=1)
    note = forms.CharField(max_length=200, required=False)

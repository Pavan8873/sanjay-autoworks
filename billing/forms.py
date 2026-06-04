from django import forms
from .models import ManualCharge, Invoice


class UppercaseMixin:
    def clean(self):
        cleaned = super().clean()
        for key, value in cleaned.items():
            if isinstance(value, str):
                cleaned[key] = value.upper().strip()
        return cleaned


class ManualChargeForm(UppercaseMixin, forms.ModelForm):
    class Meta:
        model = ManualCharge
        fields = ["description", "amount"]


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ["payment_method", "notes"]


class InvoiceEditForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ["gst_rate", "payment_method", "paid", "notes"]

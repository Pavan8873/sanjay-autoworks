from django import forms
from .models import Reminder


class UppercaseMixin:
    def clean(self):
        cleaned = super().clean()
        for key, value in cleaned.items():
            if isinstance(value, str):
                cleaned[key] = value.upper().strip()
        return cleaned


class ReminderForm(UppercaseMixin, forms.ModelForm):
    class Meta:
        model = Reminder
        fields = ["reminder_type", "due_date", "channel", "message"]
        widgets = {"due_date": forms.DateInput(attrs={"type": "date"})}

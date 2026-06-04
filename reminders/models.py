from django.db import models
from customers.models import Vehicle


class Reminder(models.Model):
    REMINDER_TYPES = [
        ("service", "Service Due"),
        ("insurance", "Insurance Renewal"),
        ("rc", "Registration Renewal"),
        ("pollution", "Pollution Certificate"),
    ]
    CHANNELS = [
        ("email", "Email"),
        ("sms", "SMS"),
        ("whatsapp", "WhatsApp"),
    ]
    STATUS = [
        ("pending", "Pending"),
        ("sent", "Sent"),
        ("dismissed", "Dismissed"),
    ]
    vehicle = models.ForeignKey(Vehicle, related_name="reminders", on_delete=models.CASCADE)
    reminder_type = models.CharField(max_length=20, choices=REMINDER_TYPES)
    due_date = models.DateField()
    channel = models.CharField(max_length=20, choices=CHANNELS, default="email")
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["due_date"]

    def __str__(self):
        return f"{self.get_reminder_type_display()} - {self.vehicle.registration_number} ({self.due_date})"

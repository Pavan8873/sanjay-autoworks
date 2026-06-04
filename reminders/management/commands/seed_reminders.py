"""
Django management command to create sample reminder data for testing.

Usage:
    python manage.py seed_reminders
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, date
from reminders.models import Reminder
from customers.models import Customer, Vehicle


class Command(BaseCommand):
    help = "Create sample reminder data for testing"

    def handle(self, *args, **options):
        # Get or create sample customers and vehicles
        customers_data = [
            {
                "name": "RAHUL SHARMA",
                "phone": "+919876543210",
                "email": "rahul@example.com",
                "address": "12 MG Road, Bengaluru",
            },
            {
                "name": "PRIYA IYER",
                "phone": "+919812345678",
                "email": "priya@example.com",
                "address": "45 Brigade Road, Bengaluru",
            },
            {
                "name": "AMIT KUMAR",
                "phone": "+919899887766",
                "email": "amit@example.com",
                "address": "123 Indiranagar, Bengaluru",
            },
            {
                "name": "DEEPAK SINGH",
                "phone": "+919765432109",
                "email": "deepak@example.com",
                "address": "456 Whitefield, Bengaluru",
            },
            {
                "name": "NEHA PATEL",
                "phone": "+919654321098",
                "email": "neha@example.com",
                "address": "789 Koramangala, Bengaluru",
            },
        ]

        vehicles_data = [
            {"reg": "KA01AB1234", "make": "MAHINDRA", "model": "XUV500"},
            {"reg": "KA02CD5678", "make": "HYUNDAI", "model": "CRETA"},
            {"reg": "KA03EF9012", "make": "MARUTI", "model": "SWIFT"},
            {"reg": "KA04GH3456", "make": "TATA", "model": "NEXON"},
            {"reg": "KA05IJ7890", "make": "TOYOTA", "model": "FORTUNER"},
        ]

        today = date.today()

        # Create customers and vehicles
        for i, cust_data in enumerate(customers_data):
            customer, _ = Customer.objects.get_or_create(
                phone=cust_data["phone"],
                defaults={
                    "name": cust_data["name"],
                    "email": cust_data["email"],
                    "address": cust_data["address"],
                },
            )

            vehicle_info = vehicles_data[i]
            vehicle, _ = Vehicle.objects.get_or_create(
                registration_number=vehicle_info["reg"],
                defaults={
                    "customer": customer,
                    "make": vehicle_info["make"],
                    "model": vehicle_info["model"],
                    "vehicle_type": "car",
                },
            )

        # Create sample reminders
        sample_reminders = [
            # Pending Service Due - Due Soon (3 days)
            {
                "vehicle_reg": "KA01AB1234",
                "reminder_type": "service",
                "due_date": today + timedelta(days=3),
                "channel": "whatsapp",
                "status": "pending",
            },
            # Pending Insurance - Due in 10 days
            {
                "vehicle_reg": "KA02CD5678",
                "reminder_type": "insurance",
                "due_date": today + timedelta(days=10),
                "channel": "email",
                "status": "pending",
            },
            # Sent RC Renewal - Sent 1 day ago
            {
                "vehicle_reg": "KA03EF9012",
                "reminder_type": "rc",
                "due_date": today + timedelta(days=15),
                "channel": "whatsapp",
                "status": "sent",
                "sent_at": timezone.now() - timedelta(days=1),
            },
            # Dismissed Pollution Certificate
            {
                "vehicle_reg": "KA04GH3456",
                "reminder_type": "pollution",
                "due_date": today + timedelta(days=20),
                "channel": "sms",
                "status": "dismissed",
            },
            # Pending Service Due - Overdue (due yesterday)
            {
                "vehicle_reg": "KA05IJ7890",
                "reminder_type": "service",
                "due_date": today - timedelta(days=1),
                "channel": "whatsapp",
                "status": "pending",
            },
            # Pending Insurance - Due in 5 days
            {
                "vehicle_reg": "KA01AB1234",
                "reminder_type": "insurance",
                "due_date": today + timedelta(days=5),
                "channel": "email",
                "status": "pending",
            },
            # Sent Pollution - Sent 5 days ago
            {
                "vehicle_reg": "KA02CD5678",
                "reminder_type": "pollution",
                "due_date": today + timedelta(days=25),
                "channel": "whatsapp",
                "status": "sent",
                "sent_at": timezone.now() - timedelta(days=5),
            },
            # Pending RC - Due in 30 days
            {
                "vehicle_reg": "KA03EF9012",
                "reminder_type": "rc",
                "due_date": today + timedelta(days=30),
                "channel": "email",
                "status": "pending",
            },
        ]

        created_count = 0
        for reminder_data in sample_reminders:
            vehicle = Vehicle.objects.get(
                registration_number=reminder_data["vehicle_reg"]
            )
            
            # Extract data
            vehicle_reg = reminder_data.pop("vehicle_reg")
            sent_at = reminder_data.pop("sent_at", None)
            
            # Check if reminder already exists
            exists = Reminder.objects.filter(
                vehicle=vehicle,
                reminder_type=reminder_data["reminder_type"],
                due_date=reminder_data["due_date"],
            ).exists()
            
            if not exists:
                reminder_data["vehicle"] = vehicle
                reminder_data["message"] = ""
                
                reminder = Reminder.objects.create(**reminder_data)
                
                if sent_at:
                    reminder.sent_at = sent_at
                    reminder.save(update_fields=["sent_at"])
                
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ Created: {vehicle.registration_number} - {reminder.get_reminder_type_display()} ({reminder.get_status_display()})"
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"⚠ Skipped: {vehicle.registration_number} - {reminder_data['reminder_type']} (already exists)"
                    )
                )

        self.stdout.write("\n" + "="*60)
        self.stdout.write(
            self.style.SUCCESS(f"✓ Created {created_count} sample reminders")
        )
        self.stdout.write("\nSample data created!")
        self.stdout.write("\nYou can now view reminders at:")
        self.stdout.write("  - http://127.0.0.1:8000/reminders/")
        self.stdout.write("  - http://127.0.0.1:8000/reminders/due-soon/")

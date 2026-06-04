from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from customers.models import Customer, Vehicle
from inventory.models import Part, Supplier


class Command(BaseCommand):
    help = "Seed the database with starter data"

    def handle(self, *args, **opts):
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@example.com", "admin123")
            self.stdout.write(self.style.SUCCESS("Created superuser admin/admin123"))

        sup, _ = Supplier.objects.get_or_create(name="Bosch India", defaults={"phone": "+91 80 1234 5678"})
        seed_parts = [
            ("OIL-5W30", "Engine Oil 5W-30 (1L)", "Oils & Lubricants", 650, 40),
            ("OIL-10W40", "Engine Oil 10W-40 (1L)", "Oils & Lubricants", 580, 30),
            ("FILT-OIL-01", "Oil Filter (Universal)", "Filters", 220, 25),
            ("FILT-AIR-01", "Air Filter", "Filters", 350, 20),
            ("BRK-PAD-FR", "Brake Pad Set - Front", "Brakes", 1200, 12),
            ("BRK-PAD-RR", "Brake Pad Set - Rear", "Brakes", 1100, 10),
            ("SPK-PLG-01", "Spark Plug (set of 4)", "Ignition", 480, 15),
            ("BAT-12V-60", "Battery 12V 60Ah", "Electricals", 5800, 5),
            ("WIPE-FR", "Wiper Blade Front (pair)", "Wipers", 420, 18),
            ("COOL-1L", "Coolant (1L)", "Fluids", 320, 22),
        ]
        for sku, name, cat, price, stock in seed_parts:
            Part.objects.get_or_create(sku=sku, defaults={
                "name": name, "category": cat, "unit_price": price,
                "stock": stock, "supplier": sup, "reorder_level": 5,
            })

        c1, _ = Customer.objects.get_or_create(phone="+919876543210", defaults={"name": "Rahul Sharma", "email": "rahul@example.com", "address": "12 MG Road, Bengaluru"})
        Vehicle.objects.get_or_create(registration_number="KA01AB1234", defaults={"customer": c1, "vehicle_type": "car", "make": "Maruti Suzuki", "model": "Swift", "color": "White", "year": 2020, "odometer": 32000})
        c2, _ = Customer.objects.get_or_create(phone="+919812345678", defaults={"name": "Priya Iyer", "email": "priya@example.com", "address": "45 Brigade Rd, Bengaluru"})
        Vehicle.objects.get_or_create(registration_number="KA05CD5678", defaults={"customer": c2, "vehicle_type": "bike", "make": "Royal Enfield", "model": "Classic 350", "color": "Black", "year": 2022, "odometer": 8500})

        self.stdout.write(self.style.SUCCESS("Seed data ready."))

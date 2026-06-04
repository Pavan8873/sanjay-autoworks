from django.db import models

class Customer(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, db_index=True)
    address = models.TextField(blank=True)
    gstin = models.CharField("GSTIN", max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.phone})"


class Vehicle(models.Model):
    VEHICLE_TYPES = [
        ("car", "Car"),
        ("suv", "SUV"),
    ]
    customer = models.ForeignKey(Customer, related_name="vehicles", on_delete=models.CASCADE)
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPES, default="car")
    registration_number = models.CharField(max_length=20, unique=True)
    make = models.CharField(max_length=80)
    model = models.CharField(max_length=80)
    color = models.CharField(max_length=40, blank=True)
    year = models.PositiveIntegerField(null=True, blank=True)
    engine_number = models.CharField(max_length=60, blank=True)
    chassis_number = models.CharField(max_length=60, blank=True)
    odometer = models.PositiveIntegerField(default=0, help_text="Last recorded km")
    insurance_expiry = models.DateField(null=True, blank=True)
    pollution_expiry = models.DateField(null=True, blank=True)
    rc_expiry = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.registration_number} - {self.make} {self.model}"

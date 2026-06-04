from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from customers.models import Customer, Vehicle
from inventory.models import Part

WA_CHOICES = [
    ("ok", "OK"),
    ("nw", "Not working/missing"),
    ("dd", "Dent/Damage/Scratch/Dots"),
]

CS_ITEMS = [
    ("engine_oil", "Engine Oil"),
    ("brake_fluid", "Brake Fluid"),
    ("coolant", "Coolant"),
    ("battery", "Battery"),
    ("air_filter", "Air Filter"),
    ("ac_filter", "AC Filter"),
    ("fuel_filter", "Fuel Filter"),
    ("head_lights", "Head Lights"),
    ("tail_lamps", "Tail Lamps"),
    ("transmission_oil", "Transmission Oil"),
    ("differential_oil", "Differential Oil"),
    ("suspension", "Suspension"),
    ("brake_disc", "Brake Disc / Rotors"),
    ("brake_drum", "Brake Drum"),
    ("tyres", "Tyres"),
    ("horn", "Horn"),
    ("ac_heater", "AC / Heater"),
    ("wipers", "Wipers / Washer Fluid"),
]


class JobCard(models.Model):
    STATUS_CHOICES = [
        ("open", "Open"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("billed", "Billed"),
        ("cancelled", "Cancelled"),
    ]
    job_number = models.CharField(max_length=20, unique=True, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="jobcards")
    vehicle = models.ForeignKey(Vehicle, on_delete=models.PROTECT, related_name="jobcards")
    mechanic = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    service_advisor = models.CharField(max_length=100, blank=True)
    odometer_in = models.PositiveIntegerField(null=True, blank=True)
    battery_condition = models.CharField(max_length=100, blank=True)
    tyres_condition = models.CharField(max_length=100, blank=True)
    inspection_notes = models.TextField(blank=True, help_text="Issues observed during inspection")
    work_to_do = models.TextField(blank=True, help_text="Job description / work requested")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")
    labor_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    labor_rate = models.DecimalField(max_digits=8, decimal_places=2, default=0, help_text="Per hour")

    wa_windshield = models.CharField(max_length=4, choices=WA_CHOICES, blank=True, default="")
    wa_toolkit = models.CharField(max_length=4, choices=WA_CHOICES, blank=True, default="")
    wa_jack = models.CharField(max_length=4, choices=WA_CHOICES, blank=True, default="")
    wa_spare_wheel = models.CharField(max_length=4, choices=WA_CHOICES, blank=True, default="")
    wa_wheel_cap = models.CharField(max_length=4, choices=WA_CHOICES, blank=True, default="")
    wa_audio = models.CharField(max_length=4, choices=WA_CHOICES, blank=True, default="")
    wa_cd_pendrive = models.CharField(max_length=4, choices=WA_CHOICES, blank=True, default="")
    wa_mat = models.CharField(max_length=4, choices=WA_CHOICES, blank=True, default="")
    wa_warranty_book = models.CharField(max_length=4, choices=WA_CHOICES, blank=True, default="")
    wa_idol = models.CharField(max_length=4, choices=WA_CHOICES, blank=True, default="")
    wa_perfume = models.CharField(max_length=4, choices=WA_CHOICES, blank=True, default="")
    wa_central_locking = models.CharField(max_length=4, choices=WA_CHOICES, blank=True, default="")
    wa_steering = models.CharField(max_length=4, choices=WA_CHOICES, blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.job_number:
            super().save(*args, **kwargs)
            self.job_number = f"JC-{self.created_at.strftime('%Y%m')}-{self.pk:05d}"
            super().save(update_fields=["job_number"])
        else:
            super().save(*args, **kwargs)

    @property
    def parts_total(self):
        inv = sum((i.line_total for i in self.parts_used.all()), Decimal("0"))
        manual = sum((i.line_total for i in self.manual_parts.all()), Decimal("0"))
        return inv + manual

    @property
    def labor_total(self):
        from django.db.models import Sum
        result = self.labour_charges.aggregate(total=Sum("amount"))["total"]
        return result if result is not None else Decimal("0")

    def __str__(self):
        return self.job_number or f"JobCard #{self.pk}"


class JobCardPart(models.Model):
    jobcard = models.ForeignKey(JobCard, related_name="parts_used", on_delete=models.CASCADE)
    part = models.ForeignKey(Part, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def line_total(self):
        return self.quantity * self.unit_price


class ManualJobPart(models.Model):
    jobcard = models.ForeignKey(JobCard, related_name="manual_parts", on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def line_total(self):
        return self.quantity * self.unit_price


class LabourCharge(models.Model):
    PRESETS = [
        ("General Service", 500),
        ("Oil Change", 250),
        ("Wheel Alignment", 400),
        ("AC Service", 600),
        ("Wash & Clean", 200),
        ("Diagnostics", 300),
    ]
    jobcard = models.ForeignKey(JobCard, related_name="labour_charges", on_delete=models.CASCADE)
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)


class ServiceChecksheet(models.Model):
    jobcard = models.OneToOneField(JobCard, on_delete=models.CASCADE, related_name="checksheet")
    checklist = models.JSONField(default=dict, blank=True)
    battery_voltage = models.CharField(max_length=20, blank=True)
    battery_cell_1 = models.CharField(max_length=20, blank=True)
    battery_cell_2 = models.CharField(max_length=20, blank=True)
    battery_cell_3 = models.CharField(max_length=20, blank=True)
    battery_cell_4 = models.CharField(max_length=20, blank=True)
    battery_cell_5 = models.CharField(max_length=20, blank=True)
    battery_cell_6 = models.CharField(max_length=20, blank=True)
    brake_front_lhs = models.CharField(max_length=20, blank=True)
    brake_front_rhs = models.CharField(max_length=20, blank=True)
    brake_rear_lhs = models.CharField(max_length=20, blank=True)
    brake_rear_rhs = models.CharField(max_length=20, blank=True)
    brake_liners = models.TextField(blank=True)
    diagnostics_report = models.TextField(blank=True)
    job_remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Checksheet for {self.jobcard}"

from decimal import Decimal
from django.conf import settings
from django.db import models
from jobcards.models import JobCard


class Invoice(models.Model):
    PAYMENT_METHODS = [
        ("cash", "Cash"),
        ("upi", "UPI"),
        ("card", "Card"),
        ("bank", "Bank Transfer"),
        ("pending", "Pending"),
    ]
    invoice_number = models.CharField(max_length=20, unique=True, blank=True)
    jobcard = models.OneToOneField(JobCard, on_delete=models.CASCADE, related_name="invoice")
    parts_subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    labor_subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    manual_subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=18)
    gst_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default="pending")
    paid = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            super().save(*args, **kwargs)
            self.invoice_number = f"INV-{self.created_at.strftime('%Y%m')}-{self.pk:05d}"
            super().save(update_fields=["invoice_number"])
        else:
            super().save(*args, **kwargs)

    def recalculate(self):
        inv_parts = sum((p.line_total for p in self.jobcard.parts_used.all()), Decimal("0"))
        manual_parts = sum((p.line_total for p in self.jobcard.manual_parts.all()), Decimal("0"))
        labor = Decimal(str(self.jobcard.labor_total))
        other = sum((c.amount for c in self.manual_charges.all()), Decimal("0"))

        self.parts_subtotal = inv_parts + manual_parts
        self.labor_subtotal = labor
        self.manual_subtotal = other
        sub = self.parts_subtotal + labor + other
        gst = (sub * self.gst_rate / Decimal("100")).quantize(Decimal("0.01"))
        self.subtotal = sub
        self.gst_amount = gst
        self.total = (sub + gst).quantize(Decimal("0.01"))
        self.save()

    def __str__(self):
        return self.invoice_number or f"Invoice #{self.pk}"


class ManualCharge(models.Model):
    PRESETS = [
        ("Miscellaneous", 200),
        ("Pickup & Drop", 250),
        ("Towing Charge", 500),
    ]
    invoice = models.ForeignKey(Invoice, related_name="manual_charges", on_delete=models.CASCADE)
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

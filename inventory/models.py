import io
import qrcode
from django.core.files.base import ContentFile
from django.db import models


class Supplier(models.Model):
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Part(models.Model):
    sku = models.CharField("SKU / Part Code", max_length=60, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=80, blank=True)
    supplier = models.ForeignKey(Supplier, null=True, blank=True, on_delete=models.SET_NULL)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock = models.IntegerField(default=0)
    reorder_level = models.IntegerField(default=5)
    qr_code = models.ImageField(upload_to="qrcodes/", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.qr_code:
            img = qrcode.make(self.sku)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            self.qr_code.save(f"{self.sku}.png", ContentFile(buf.getvalue()), save=False)
            super().save(update_fields=["qr_code"])

    @property
    def low_stock(self):
        return self.stock <= self.reorder_level

    def __str__(self):
        return f"{self.sku} - {self.name}"


class StockMovement(models.Model):
    MOVEMENT_TYPES = [
        ("in", "Stock In"),
        ("out", "Stock Out"),
        ("adjust", "Adjustment"),
    ]
    part = models.ForeignKey(Part, related_name="movements", on_delete=models.CASCADE)
    movement_type = models.CharField(max_length=10, choices=MOVEMENT_TYPES)
    quantity = models.IntegerField()
    note = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

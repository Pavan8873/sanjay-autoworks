from django.contrib import admin
from .models import Invoice, ManualCharge
admin.site.register(Invoice)
admin.site.register(ManualCharge)

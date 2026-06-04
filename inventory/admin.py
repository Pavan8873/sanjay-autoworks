from django.contrib import admin
from .models import Part, Supplier, StockMovement
admin.site.register(Part)
admin.site.register(Supplier)
admin.site.register(StockMovement)

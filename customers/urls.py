from django.urls import path
from . import views

app_name = "customers"

urlpatterns = [
    path("", views.list_customers, name="list"),
    path("new/", views.quick_register, name="new"),
    path("<int:pk>/", views.detail, name="detail"),
    path("<int:pk>/edit/", views.edit, name="edit"),
    path("<int:pk>/delete/", views.delete, name="delete"),
    path("<int:pk>/vehicle/new/", views.add_vehicle, name="add_vehicle"),
    path("vehicle/<int:pk>/", views.vehicle_detail, name="vehicle_detail"),
    path("vehicle/<int:pk>/edit/", views.edit_vehicle, name="edit_vehicle"),
    path("vehicle/<int:pk>/delete/", views.delete_vehicle, name="delete_vehicle"),
    path("api/lookup/phone/", views.api_lookup_phone, name="api_lookup_phone"),
    path("api/lookup/vehicle/", views.api_lookup_vehicle, name="api_lookup_vehicle"),
]

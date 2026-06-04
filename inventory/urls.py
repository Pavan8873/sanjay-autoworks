from django.urls import path
from . import views

app_name = "inventory"

urlpatterns = [
    path("", views.list_parts, name="list"),
    path("new/", views.create_part, name="new"),
    path("<int:pk>/", views.detail, name="detail"),
    path("<int:pk>/edit/", views.edit, name="edit"),
    path("<int:pk>/delete/", views.delete, name="delete"),
    path("<int:pk>/restock/", views.restock, name="restock"),
    path("scan/", views.scan, name="scan"),
    path("api/lookup/", views.api_lookup, name="api_lookup"),
    path("suppliers/", views.suppliers, name="suppliers"),
]

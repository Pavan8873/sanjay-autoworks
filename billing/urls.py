from django.urls import path
from . import views

app_name = "billing"

urlpatterns = [
    path("", views.list_invoices, name="list"),
    path("<int:pk>/", views.detail, name="detail"),
    path("<int:pk>/edit/", views.edit_invoice, name="edit"),
    path("<int:pk>/delete/", views.delete_invoice, name="delete"),
    path("<int:pk>/add-charge/", views.add_charge, name="add_charge"),
    path("<int:pk>/remove-charge/<int:charge_id>/", views.remove_charge, name="remove_charge"),
    path("<int:pk>/pay/", views.mark_paid, name="pay"),
    path("<int:pk>/print/", views.print_invoice, name="print"),
]

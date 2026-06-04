from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("reports/", views.reports, name="reports"),
    path("reports/pdf/", views.reports_pdf, name="reports_pdf"),
    path("reports/excel/", views.reports_excel, name="reports_excel"),
]

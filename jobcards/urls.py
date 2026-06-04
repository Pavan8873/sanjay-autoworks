from django.urls import path
from . import views

app_name = "jobcards"

urlpatterns = [
    path("", views.list_jobs, name="list"),
    path("new/", views.create, name="new"),
    path("<int:pk>/", views.detail, name="detail"),
    path("<int:pk>/edit/", views.edit, name="edit"),
    path("<int:pk>/delete/", views.delete, name="delete"),
    path("<int:pk>/add-part/", views.add_part, name="add_part"),
    path("<int:pk>/remove-part/<int:part_id>/", views.remove_part, name="remove_part"),
    path("<int:pk>/add-manual-part/", views.add_manual_part, name="add_manual_part"),
    path("<int:pk>/remove-manual-part/<int:part_id>/", views.remove_manual_part, name="remove_manual_part"),
    path("<int:pk>/add-labour/", views.add_labour, name="add_labour"),
    path("<int:pk>/remove-labour/<int:charge_id>/", views.remove_labour, name="remove_labour"),
    path("<int:pk>/complete/", views.complete, name="complete"),
    path("<int:pk>/print/", views.print_jobcard, name="print_jobcard"),
    path("<int:pk>/setup/", views.setup, name="setup"),
    path("<int:pk>/checksheet-step/", views.checksheet_step, name="checksheet_step"),
    path("<int:pk>/parts/", views.parts_step, name="parts_step"),
    path("<int:pk>/update-labour/", views.update_labour, name="update_labour"),
    path("<int:pk>/checksheet/", views.checksheet_edit, name="checksheet"),
    path("<int:pk>/checksheet/print/", views.print_checksheet, name="print_checksheet"),
    path("<int:pk>/whatsapp-send/", views.whatsapp_send, name="whatsapp_send"),
    path("<int:pk>/send-sms/", views.send_sms_view, name="send_sms"),
]

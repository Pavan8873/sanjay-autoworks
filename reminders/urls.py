from django.urls import path
from . import views

app_name = "reminders"

urlpatterns = [
    path("", views.list_reminders, name="list"),
    path("due-soon/", views.due_soon, name="due_soon"),
    path("<int:pk>/send/", views.send, name="send"),
    path("<int:pk>/send-whatsapp/", views.send_whatsapp_link, name="send_whatsapp"),
    path("<int:pk>/mark-sent/", views.mark_sent, name="mark_sent"),
    path("<int:pk>/dismiss/", views.dismiss, name="dismiss"),
    path("new/<int:vehicle_id>/", views.create, name="new"),
    path("bulk/send-whatsapp/", views.bulk_send_whatsapp, name="bulk_send_whatsapp"),
    path("bulk/dismiss/", views.bulk_dismiss, name="bulk_dismiss"),
]

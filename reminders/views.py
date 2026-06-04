import urllib.parse
from datetime import timedelta

from django.conf import settings as conf
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .models import Reminder
from .forms import ReminderForm
from customers.models import Vehicle


def _build_reminder_message(r) -> str:
    customer = r.vehicle.customer
    v = r.vehicle
    shop = getattr(conf, "SHOP_NAME", "Sanjay Auto Works")
    phone = getattr(conf, "SHOP_PHONE", "")
    reminder_type = r.get_reminder_type_display()
    due_date = r.due_date.strftime('%d %b %Y') if r.due_date else 'soon'
    
    return (
        f"Dear {customer.name},\n\n"
        f"This is a service reminder from {shop}.\n\n"
        f"Your vehicle {v.registration_number} ({v.make} {v.model}) is due for {reminder_type} on {due_date}.\n\n"
        f"Please contact us at your earliest convenience to schedule an appointment:\n\n"
        f"Phone: {phone}\n\n"
        f"Thank you for your business.\n\n"
        f"{shop}"
    )


def _wa_link(phone: str, message: str) -> str:
    from core.whatsapp import wa_me_link
    return wa_me_link(phone, message)


@login_required
def list_reminders(request):
    status = request.GET.get("status", "pending")
    reminders = Reminder.objects.select_related("vehicle__customer").order_by("due_date")
    if status:
        reminders = reminders.filter(status=status)
    return render(request, "reminders/list.html", {
        "reminders": reminders,
        "status": status,
        "sms_enabled": getattr(conf, "SMS_ENABLED", False),
        "wa_enabled": getattr(conf, "WHATSAPP_ENABLED", False),
    })


@login_required
def due_soon(request):
    """Bulk WhatsApp reminder dashboard — shows service due soon."""
    from jobcards.models import JobCard

    days = int(request.GET.get("days", 7))
    today = timezone.now().date()
    cutoff = today + timedelta(days=days)

    # --- Auto-generate missing service reminders ---
    # Find vehicles whose last completed job was > 330 days ago with no pending service reminder
    generated = 0
    all_vehicles = Vehicle.objects.prefetch_related(
        "jobcards", "reminders"
    ).select_related("customer")

    for v in all_vehicles:
        last_job = (
            v.jobcards.filter(status__in=("completed", "billed"))
            .order_by("-created_at")
            .first()
        )
        if not last_job:
            continue
        next_service = last_job.created_at.date() + timedelta(days=365)
        if next_service > cutoff:
            continue
        # Check if a pending service reminder already exists for this vehicle
        already = v.reminders.filter(
            reminder_type="service", status="pending"
        ).exists()
        if already:
            continue
        # Create one
        Reminder.objects.create(
            vehicle=v,
            reminder_type="service",
            due_date=next_service,
            channel="whatsapp",
            message="",
            status="pending",
        )
        generated += 1

    if generated:
        messages.success(
            request, f"✅ {generated} new service reminder(s) auto-generated."
        )

    # --- Fetch all pending service reminders due within window ---
    due_reminders = (
        Reminder.objects.filter(
            reminder_type="service",
            status="pending",
            due_date__lte=cutoff,
        )
        .select_related("vehicle__customer")
        .order_by("due_date")
    )

    rows = []
    for r in due_reminders:
        msg = _build_reminder_message(r)
        link = _wa_link(r.vehicle.customer.phone, msg)
        days_left = (r.due_date - today).days
        rows.append({
            "reminder": r,
            "customer": r.vehicle.customer,
            "vehicle": r.vehicle,
            "days_left": days_left,
            "urgent": days_left <= 3,
            "overdue": days_left < 0,
            "message": msg,
            "wa_link": link,
        })

    return render(request, "reminders/due_soon.html", {
        "rows": rows,
        "days": days,
        "today": today,
    })


@login_required
def send(request, pk):
    """Send reminder via SMS or Twilio WhatsApp (server-side)."""
    from core.whatsapp import send_sms, send_whatsapp_message

    r = get_object_or_404(Reminder, pk=pk)
    channel = request.POST.get("channel", r.channel)
    body = _build_reminder_message(r)
    phone = r.vehicle.customer.phone

    if channel == "sms":
        ok, reason = send_sms(phone, body)
    elif channel == "whatsapp":
        ok, reason = send_whatsapp_message(phone, body)
    else:
        ok, reason = False, "Select SMS or WhatsApp"

    if ok:
        r.status = "sent"
        r.sent_at = timezone.now()
        r.save()
        messages.success(request, f"Reminder sent via {channel.upper()} to {phone}.")
    else:
        messages.error(request, f"Could not send {channel.upper()}: {reason}")

    return redirect("reminders:list")


@login_required
def send_whatsapp_link(request, pk):
    """Open WhatsApp via wa.me link (no Twilio needed) and mark reminder sent."""
    r = get_object_or_404(Reminder, pk=pk)
    body = _build_reminder_message(r)
    link = _wa_link(r.vehicle.customer.phone, body)

    r.status = "sent"
    r.sent_at = timezone.now()
    r.save()

    if link:
        return redirect(link)
    messages.error(request, "Could not build WhatsApp link — phone number missing.")
    return redirect("reminders:list")


@login_required
def mark_sent(request, pk):
    """Mark a reminder as sent (used after manual WhatsApp from due_soon page)."""
    r = get_object_or_404(Reminder, pk=pk)
    if request.method == "POST":
        r.status = "sent"
        r.sent_at = timezone.now()
        r.save()
    return redirect("reminders:due_soon")


@login_required
def dismiss(request, pk):
    r = get_object_or_404(Reminder, pk=pk)
    r.status = "dismissed"
    r.save()
    next_url = request.POST.get("next", "reminders:list")
    if next_url == "due_soon":
        return redirect("reminders:due_soon")
    return redirect("reminders:list")


@login_required
def create(request, vehicle_id):
    vehicle = get_object_or_404(Vehicle, pk=vehicle_id)
    if request.method == "POST":
        form = ReminderForm(request.POST)
        if form.is_valid():
            r = form.save(commit=False)
            r.vehicle = vehicle
            r.save()
            return redirect("customers:vehicle_detail", pk=vehicle.pk)
    else:
        form = ReminderForm()
    return render(request, "reminders/form.html", {"form": form, "vehicle": vehicle})


@login_required
def bulk_send_whatsapp(request):
    """Send WhatsApp to multiple selected reminders."""
    from core.whatsapp import send_whatsapp_message
    
    if request.method == "POST":
        reminder_ids = request.POST.getlist("reminder_ids")
        if not reminder_ids:
            messages.error(request, "No reminders selected.")
            return redirect("reminders:list")
        
        reminders = Reminder.objects.filter(
            pk__in=reminder_ids,
            status="pending"
        ).select_related("vehicle__customer")
        
        sent_count = 0
        failed_count = 0
        
        for r in reminders:
            msg = _build_reminder_message(r)
            phone = r.vehicle.customer.phone
            
            # Try to send via Twilio API
            ok, reason = send_whatsapp_message(phone, msg)
            
            if ok:
                r.status = "sent"
                r.sent_at = timezone.now()
                r.save()
                sent_count += 1
            else:
                failed_count += 1
        
        if sent_count > 0:
            messages.success(request, f"✓ {sent_count} WhatsApp message(s) sent successfully!")
        if failed_count > 0:
            messages.warning(request, f"⚠ {failed_count} message(s) failed to send.")
        
        return redirect("reminders:list")
    
    return redirect("reminders:list")


@login_required
def bulk_dismiss(request):
    """Dismiss multiple selected reminders."""
    if request.method == "POST":
        reminder_ids = request.POST.getlist("reminder_ids")
        if not reminder_ids:
            messages.error(request, "No reminders selected.")
            return redirect("reminders:list")
        
        count = Reminder.objects.filter(
            pk__in=reminder_ids
        ).update(status="dismissed")
        
        messages.success(request, f"✓ {count} reminder(s) dismissed.")
        return redirect("reminders:list")
    
    return redirect("reminders:list")

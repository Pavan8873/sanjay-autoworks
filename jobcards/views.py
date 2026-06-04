import json
from decimal import Decimal
from datetime import date, timedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .forms import JobCardForm, AddPartForm, ChecksheetForm, WA_FIELDS
from .models import JobCard, JobCardPart, ManualJobPart, LabourCharge, ServiceChecksheet, CS_ITEMS
from django.db.models import Sum
from inventory.models import Part, StockMovement
from billing.models import Invoice
from reminders.models import Reminder
from customers.models import Customer, Vehicle
from core.whatsapp import send_jobcard_created_whatsapp


def _form_context(form, title):
    vehicles = list(Vehicle.objects.select_related("customer").values(
        "id", "make", "model", "registration_number",
        "chassis_number", "engine_number", "odometer", "customer_id",
    ))
    customers = list(Customer.objects.values("id", "name", "phone", "address"))
    return {
        "form": form,
        "title": title,
        "vehicles_json": json.dumps(vehicles),
        "customers_json": json.dumps(customers),
        "wa_fields": [(label, form[fname]) for fname, label in WA_FIELDS],
        "today": date.today(),
    }


@login_required
def list_jobs(request):
    status = request.GET.get("status", "")
    jobs = JobCard.objects.select_related("customer", "vehicle").order_by("-created_at")
    if status:
        jobs = jobs.filter(status=status)
    return render(request, "jobcards/list.html", {"jobs": jobs, "status": status})


@login_required
def create(request):
    if request.method == "POST":
        form = JobCardForm(request.POST)
        if form.is_valid():
            jc = form.save()
            send_jobcard_created_whatsapp(jc)
            messages.success(request, f"Job Card {jc.job_number} created.")
            return redirect("jobcards:setup", pk=jc.pk)
    else:
        form = JobCardForm()
    return render(request, "jobcards/form.html", _form_context(form, "New Job Card"))


@login_required
def detail(request, pk):
    jc = get_object_or_404(JobCard, pk=pk)
    add_form = AddPartForm()
    popular = (Part.objects
               .annotate(used=Sum("jobcardpart__quantity"))
               .filter(stock__gt=0)
               .order_by("-used", "name")[:8])
    wa_display = [(label, getattr(jc, fname, "")) for fname, label in WA_FIELDS]
    has_checksheet = hasattr(jc, "checksheet")
    return render(request, "jobcards/detail.html", {
        "job": jc, "add_form": add_form, "popular_parts": popular,
        "wa_display": wa_display, "has_checksheet": has_checksheet,
    })


@login_required
def edit(request, pk):
    jc = get_object_or_404(JobCard, pk=pk)
    if request.method == "POST":
        form = JobCardForm(request.POST, instance=jc)
        if form.is_valid():
            form.save()
            return redirect("jobcards:detail", pk=pk)
    else:
        form = JobCardForm(instance=jc)
    return render(request, "jobcards/form.html", _form_context(form, f"Edit {jc.job_number}"))


@login_required
def setup(request, pk):
    """Step 2 — Job Card only."""
    jc = get_object_or_404(JobCard, pk=pk)

    vehicles = list(Vehicle.objects.select_related("customer").values(
        "id", "make", "model", "registration_number",
        "chassis_number", "engine_number", "odometer", "customer_id",
    ))
    customers = list(Customer.objects.values("id", "name", "phone", "address"))

    if request.method == "POST":
        jc_form = JobCardForm(request.POST, prefix="jc", instance=jc)
        if jc_form.is_valid():
            jc_form.save()
            messages.success(request, "Job Card saved.")
        action = request.POST.get("_action", "save")
        if action == "next":
            return redirect("jobcards:checksheet_step", pk=jc.pk)
        return redirect("jobcards:setup", pk=jc.pk)

    jc_form = JobCardForm(prefix="jc", instance=jc)
    wa_rows = [(label, jc_form[fname]) for fname, label in WA_FIELDS]

    return render(request, "jobcards/setup.html", {
        "job": jc,
        "jc_form": jc_form,
        "wa_rows": wa_rows,
        "vehicles_json": json.dumps(vehicles),
        "customers_json": json.dumps(customers),
    })


@login_required
def checksheet_step(request, pk):
    """Step 3 — Service Checksheet only."""
    jc = get_object_or_404(JobCard, pk=pk)
    cs_instance = ServiceChecksheet.objects.filter(jobcard=jc).first()

    if request.method == "POST":
        cs_form = ChecksheetForm(request.POST, prefix="cs", instance=cs_instance)
        if cs_form.is_valid():
            cd = cs_form.cleaned_data
            checklist = {}
            for key, label in CS_ITEMS:
                checklist[key] = {
                    "status": cd.get(f"cs_{key}", ""),
                    "remarks": cd.get(f"cs_{key}_rem", ""),
                }
            if cs_instance is None:
                cs_instance = ServiceChecksheet(jobcard=jc)
            cs_instance.checklist = checklist
            for field in ("battery_voltage", "battery_cell_1", "battery_cell_2",
                          "battery_cell_3", "battery_cell_4", "battery_cell_5",
                          "battery_cell_6", "brake_front_lhs", "brake_front_rhs",
                          "brake_rear_lhs", "brake_rear_rhs", "brake_liners",
                          "diagnostics_report", "job_remarks"):
                setattr(cs_instance, field, cd.get(field, ""))
            cs_instance.save()
            messages.success(request, "Checksheet saved.")
        action = request.POST.get("_action", "save")
        if action == "next":
            return redirect("jobcards:parts_step", pk=jc.pk)
        return redirect("jobcards:checksheet_step", pk=jc.pk)

    cs_form = ChecksheetForm(prefix="cs", instance=cs_instance)
    cs_rows = []
    for key, label in CS_ITEMS:
        cs_rows.append((label, cs_form[f"cs_{key}"], cs_form[f"cs_{key}_rem"]))

    return render(request, "jobcards/checksheet_step.html", {
        "job": jc,
        "cs_form": cs_form,
        "cs_rows": cs_rows,
        "has_checksheet": cs_instance is not None,
    })


@login_required
def print_jobcard(request, pk):
    jc = get_object_or_404(JobCard, pk=pk)
    wa_display = [(label, getattr(jc, fname, "")) for fname, label in WA_FIELDS]
    return render(request, "jobcards/print_jobcard.html", {
        "job": jc, "wa_display": wa_display,
    })


@login_required
def checksheet_edit(request, pk):
    jc = get_object_or_404(JobCard, pk=pk)
    instance = ServiceChecksheet.objects.filter(jobcard=jc).first()
    if request.method == "POST":
        form = ChecksheetForm(request.POST, instance=instance)
        if form.is_valid():
            cd = form.cleaned_data
            checklist = {}
            for key, label in CS_ITEMS:
                checklist[key] = {
                    "status": cd.get(f"cs_{key}", ""),
                    "remarks": cd.get(f"cs_{key}_rem", ""),
                }
            if instance is None:
                instance = ServiceChecksheet(jobcard=jc)
            instance.checklist = checklist
            for field in ("battery_voltage", "battery_cell_1", "battery_cell_2",
                          "battery_cell_3", "battery_cell_4", "battery_cell_5",
                          "battery_cell_6", "brake_front_lhs", "brake_front_rhs",
                          "brake_rear_lhs", "brake_rear_rhs", "brake_liners",
                          "diagnostics_report", "job_remarks"):
                setattr(instance, field, cd.get(field, ""))
            instance.save()
            messages.success(request, "Service checksheet saved.")
            return redirect("jobcards:print_checksheet", pk=pk)
    else:
        form = ChecksheetForm(instance=instance)
    cs_rows = []
    for key, label in CS_ITEMS:
        cs_rows.append((label, form[f"cs_{key}"], form[f"cs_{key}_rem"]))
    return render(request, "jobcards/checksheet_form.html", {
        "job": jc, "form": form, "cs_rows": cs_rows,
    })


@login_required
def print_checksheet(request, pk):
    jc = get_object_or_404(JobCard, pk=pk)
    cs = get_object_or_404(ServiceChecksheet, jobcard=jc)
    cs_rows = []
    for key, label in CS_ITEMS:
        item = cs.checklist.get(key, {})
        cs_rows.append({
            "label": label,
            "status": item.get("status", ""),
            "remarks": item.get("remarks", ""),
        })
    return render(request, "jobcards/print_checksheet.html", {
        "job": jc, "cs": cs, "cs_rows": cs_rows,
    })


@login_required
def parts_step(request, pk):
    """Step 4 — Parts, Manual Parts & Labour Charges."""
    jc = get_object_or_404(JobCard, pk=pk)
    add_form = AddPartForm()
    popular = (Part.objects
               .annotate(used=Sum("jobcardpart__quantity"))
               .filter(stock__gt=0)
               .order_by("-used", "name")[:8])
    labour_charges = jc.labour_charges.all()
    manual_parts = jc.manual_parts.all()
    parts_total = jc.parts_total
    labor_total = jc.labor_total
    subtotal = parts_total + labor_total
    return render(request, "jobcards/parts.html", {
        "job": jc,
        "add_form": add_form,
        "popular_parts": popular,
        "labour_charges": labour_charges,
        "manual_parts": manual_parts,
        "labour_presets": LabourCharge.PRESETS,
        "parts_total": parts_total,
        "labor_total": labor_total,
        "subtotal": subtotal,
    })


@login_required
def add_part(request, pk):
    jc = get_object_or_404(JobCard, pk=pk)
    next_view = request.GET.get("next", "detail")
    form = AddPartForm(request.POST)
    if form.is_valid():
        part = None
        if form.cleaned_data.get("part_id"):
            part = Part.objects.filter(pk=form.cleaned_data["part_id"]).first()
        if not part and form.cleaned_data.get("sku"):
            part = Part.objects.filter(sku=form.cleaned_data["sku"]).first()
        if not part:
            messages.error(request, "Part not found. Check SKU/QR code.")
            return redirect("jobcards:parts_step" if next_view == "wizard" else "jobcards:detail", pk=pk)
        qty = form.cleaned_data["quantity"]
        if part.stock < qty:
            messages.error(request, f"Insufficient stock for {part.name}. Available: {part.stock}")
            return redirect("jobcards:parts_step" if next_view == "wizard" else "jobcards:detail", pk=pk)
        JobCardPart.objects.create(jobcard=jc, part=part, quantity=qty, unit_price=part.unit_price)
        part.stock -= qty
        part.save()
        StockMovement.objects.create(part=part, movement_type="out", quantity=qty, note=f"Used in {jc.job_number}")
        if jc.status == "open":
            jc.status = "in_progress"
            jc.save()
        messages.success(request, f"Added {qty} × {part.name}")
    if next_view == "wizard":
        return redirect("jobcards:parts_step", pk=pk)
    return redirect("jobcards:detail", pk=pk)


@login_required
@transaction.atomic
def remove_part(request, pk, part_id):
    jc = get_object_or_404(JobCard, pk=pk)
    next_view = request.GET.get("next", "detail")
    line = get_object_or_404(JobCardPart, pk=part_id, jobcard=jc)
    line.part.stock += line.quantity
    line.part.save()
    StockMovement.objects.create(part=line.part, movement_type="in", quantity=line.quantity, note=f"Reverted from {jc.job_number}")
    line.delete()
    messages.success(request, "Part removed and stock restored.")
    if next_view == "wizard":
        return redirect("jobcards:parts_step", pk=pk)
    return redirect("jobcards:detail", pk=pk)


@login_required
def add_manual_part(request, pk):
    """Add a manually-entered part (not from inventory)."""
    jc = get_object_or_404(JobCard, pk=pk)
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        try:
            qty = max(1, int(request.POST.get("quantity") or 1))
            price = Decimal(request.POST.get("unit_price") or "0")
        except (ValueError, TypeError):
            qty, price = 1, Decimal("0")
        if name and price > 0:
            ManualJobPart.objects.create(jobcard=jc, name=name, quantity=qty, unit_price=price)
            messages.success(request, f"Added: {name}")
        else:
            messages.error(request, "Please enter part name and a valid price.")
    return redirect("jobcards:parts_step", pk=pk)


@login_required
def remove_manual_part(request, pk, part_id):
    jc = get_object_or_404(JobCard, pk=pk)
    ManualJobPart.objects.filter(pk=part_id, jobcard=jc).delete()
    messages.success(request, "Manual part removed.")
    return redirect("jobcards:parts_step", pk=pk)


@login_required
def add_labour(request, pk):
    """Add a labour charge line."""
    jc = get_object_or_404(JobCard, pk=pk)
    if request.method == "POST":
        desc = request.POST.get("description", "").strip()
        try:
            amount = Decimal(request.POST.get("amount") or "0")
        except (ValueError, TypeError):
            amount = Decimal("0")
        if desc and amount > 0:
            LabourCharge.objects.create(jobcard=jc, description=desc, amount=amount)
            messages.success(request, f"Labour charge added: {desc}")
        else:
            messages.error(request, "Enter description and a valid amount.")
    return redirect("jobcards:parts_step", pk=pk)


@login_required
def remove_labour(request, pk, charge_id):
    jc = get_object_or_404(JobCard, pk=pk)
    LabourCharge.objects.filter(pk=charge_id, jobcard=jc).delete()
    messages.success(request, "Labour charge removed.")
    return redirect("jobcards:parts_step", pk=pk)


@login_required
def update_labour(request, pk):
    """Legacy — kept for any existing links."""
    return redirect("jobcards:parts_step", pk=pk)


@login_required
@transaction.atomic
def complete(request, pk):
    jc = get_object_or_404(JobCard, pk=pk)
    jc.status = "completed"
    jc.completed_at = timezone.now()
    jc.save()

    invoice, created = Invoice.objects.get_or_create(jobcard=jc)
    invoice.recalculate()

    Reminder.objects.get_or_create(
        vehicle=jc.vehicle,
        reminder_type="service",
        due_date=date.today() + timedelta(days=365),
        defaults={"message": f"Annual service due (last service: {jc.job_number})"},
    )
    if jc.vehicle.insurance_expiry:
        Reminder.objects.get_or_create(
            vehicle=jc.vehicle, reminder_type="insurance",
            due_date=jc.vehicle.insurance_expiry - timedelta(days=15),
            defaults={"message": "Insurance renewal coming up"},
        )
    if jc.vehicle.pollution_expiry:
        Reminder.objects.get_or_create(
            vehicle=jc.vehicle, reminder_type="pollution",
            due_date=jc.vehicle.pollution_expiry - timedelta(days=15),
            defaults={"message": "Pollution certificate renewal coming up"},
        )
    if jc.vehicle.rc_expiry:
        Reminder.objects.get_or_create(
            vehicle=jc.vehicle, reminder_type="rc",
            due_date=jc.vehicle.rc_expiry - timedelta(days=30),
            defaults={"message": "RC renewal coming up"},
        )
    messages.success(request, "Job marked complete. Invoice generated.")
    return redirect("billing:detail", pk=invoice.pk)


@login_required
def send_sms_view(request, pk):
    from django.conf import settings as conf
    from core.whatsapp import send_sms

    jc = get_object_or_404(JobCard, pk=pk)
    invoice = None
    try:
        invoice = jc.invoice
    except Exception:
        pass

    SERVICE_INTERVAL_KM = 5000
    odometer_in = jc.odometer_in or jc.vehicle.odometer or 0
    next_service_km = odometer_in + SERVICE_INTERVAL_KM if odometer_in else None
    next_service_date = (jc.completed_at.date() if jc.completed_at else date.today()) + timedelta(days=365)
    service_date_str = (jc.completed_at.strftime("%d %b %Y") if jc.completed_at else date.today().strftime("%d %b %Y"))

    sms_lines = [
        f"{conf.SHOP_NAME} | {getattr(conf, 'SHOP_PHONE', '')}",
        f"Dear {jc.customer.name},",
        f"Your {jc.vehicle.make} {jc.vehicle.model} ({jc.vehicle.registration_number}) service is complete.",
        f"Job Card: {jc.job_number} | Date: {service_date_str}",
        f"Next Service: {next_service_date.strftime('%d %b %Y')}",
    ]
    if next_service_km:
        sms_lines.append(f"Next Service KM: {next_service_km:,} km")
    sms_lines.append("Please visit us to collect your vehicle. Thank you!")
    body = " ".join(sms_lines)
    ok, reason = send_sms(jc.customer.phone, body)
    if ok:
        messages.success(request, f"SMS sent to {jc.customer.phone}.")
    else:
        messages.error(request, f"SMS not sent: {reason}")
    return redirect("jobcards:whatsapp_send", pk=pk)


@login_required
def whatsapp_send(request, pk):
    import urllib.parse
    from django.conf import settings as conf

    jc = get_object_or_404(JobCard, pk=pk)
    invoice = None
    try:
        invoice = jc.invoice
    except Exception:
        pass

    phone = jc.customer.phone or ""
    digits = "".join(c for c in phone if c.isdigit())
    country = (getattr(conf, "WHATSAPP_COUNTRY_CODE", "+91") or "+91").strip()
    country_digits = "".join(c for c in country if c.isdigit())
    if country_digits == "91" and len(digits) >= 10:
        digits = digits[-10:]
    wa_phone = f"{country_digits}{digits}" if digits else ""

    SERVICE_INTERVAL_KM = 5000
    odometer_in = jc.odometer_in or jc.vehicle.odometer or 0
    next_service_km = odometer_in + SERVICE_INTERVAL_KM if odometer_in else None
    next_service_date = (jc.completed_at.date() if jc.completed_at else date.today()) + timedelta(days=365)
    service_date_str = (jc.completed_at.strftime("%d %b %Y") if jc.completed_at else date.today().strftime("%d %b %Y"))

    work_lower = (jc.work_to_do or "").lower()
    is_general_service = "general service" in work_lower or (not jc.work_to_do and True)

    shop_name = getattr(conf, "SHOP_NAME", "SANJAY AUTOWORKS")
    shop_phone = getattr(conf, "SHOP_PHONE", "")
    shop_address = getattr(conf, "SHOP_ADDRESS", "")

    if is_general_service and invoice:
        lines = [
            f"*{shop_name}*",
            f"{shop_address}",
            f"Ph: {shop_phone}",
            "",
            f"Dear {jc.customer.name},",
            "",
            f"Your vehicle's *General Service* has been completed successfully. 🚗✅",
            "",
            "*CLIENT DETAILS*",
            f"Name    : {jc.customer.name}",
            f"Phone   : {jc.customer.phone}",
        ]
        if jc.customer.address:
            lines.append(f"Address : {jc.customer.address}")
        lines += [
            "",
            "*VEHICLE DETAILS*",
            f"Vehicle : {jc.vehicle.make} {jc.vehicle.model}",
            f"Reg No  : {jc.vehicle.registration_number}",
        ]
        if odometer_in:
            lines.append(f"Odometer: {odometer_in:,} km")
        lines += [
            "",
            "*SERVICE BILL*",
            f"Invoice : {invoice.invoice_number}",
            f"Date    : {service_date_str}",
            f"Parts   : ₹{invoice.parts_subtotal:,.2f}",
            f"Labour  : ₹{invoice.labor_subtotal:,.2f}",
        ]
        if invoice.manual_subtotal:
            lines.append(f"Charges : ₹{invoice.manual_subtotal:,.2f}")
        lines += [
            f"GST     : ₹{invoice.gst_amount:,.2f}",
            f"*TOTAL  : ₹{invoice.total:,.2f}*",
            "",
            "*NEXT SERVICE DUE*",
            f"Date    : {next_service_date.strftime('%d %b %Y')}",
        ]
        if next_service_km:
            lines.append(f"KM      : {next_service_km:,} km")
        lines += [
            "",
            "Your vehicle is ready for collection.",
            "Thank you for choosing us! 🙏",
        ]
    else:
        lines = [
            f"*{shop_name}*",
            f"Ph: {shop_phone}",
            "",
            f"Dear {jc.customer.name},",
            "",
            f"Your {jc.vehicle.make} {jc.vehicle.model} ({jc.vehicle.registration_number}) service is complete.",
            f"Job Card: {jc.job_number} | Date: {service_date_str}",
        ]
        if jc.work_to_do:
            lines.append(f"Work Done: {jc.work_to_do}")
        lines += [
            "",
            f"*Next Service Due: {next_service_date.strftime('%d %b %Y')}*",
        ]
        if next_service_km:
            lines.append(f"At: {next_service_km:,} km")
        lines += [
            "",
            "Your vehicle is ready for collection.",
            "Thank you for choosing us! 🙏",
        ]

    message = "\n".join(lines)
    wa_url = f"https://wa.me/{wa_phone}?text={urllib.parse.quote(message)}" if wa_phone else ""

    return render(request, "jobcards/whatsapp_send.html", {
        "job": jc,
        "invoice": invoice,
        "wa_url": wa_url,
        "message": message,
        "next_service_date": next_service_date,
        "next_service_km": next_service_km,
        "sms_enabled": getattr(conf, "SMS_ENABLED", False),
        "wa_enabled": getattr(conf, "WHATSAPP_ENABLED", False),
    })


@login_required
@transaction.atomic
def delete(request, pk):
    jc = get_object_or_404(JobCard, pk=pk)
    if request.method == "POST":
        job_number = jc.job_number
        for line in jc.parts_used.select_related("part").all():
            line.part.stock += line.quantity
            line.part.save()
            StockMovement.objects.create(
                part=line.part, movement_type="in", quantity=line.quantity,
                note=f"Reverted from deleted {job_number}",
            )
        jc.delete()
        messages.success(request, f"Job card {job_number} deleted.")
    return redirect("jobcards:list")

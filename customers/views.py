from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models.deletion import ProtectedError
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from .forms import CustomerForm, VehicleForm, QuickRegisterForm
from .models import Customer, Vehicle
from jobcards.models import JobCard
from core.whatsapp import send_jobcard_created_whatsapp


@login_required
def api_lookup_phone(request):
    phone = request.GET.get("phone", "").strip()
    if len(phone) < 4:
        return JsonResponse({"found": False})
    c = Customer.objects.filter(phone=phone).first() or Customer.objects.filter(phone__icontains=phone).first()
    if not c:
        return JsonResponse({"found": False})
    return JsonResponse({
        "found": True,
        "id": c.id,
        "name": c.name, "email": c.email, "address": c.address, "gstin": c.gstin,
        "vehicles": [
            {"id": v.id, "reg": v.registration_number, "make": v.make, "model": v.model,
             "type": v.vehicle_type, "color": v.color, "year": v.year, "odometer": v.odometer,
             "engine_number": v.engine_number, "chassis_number": v.chassis_number}
            for v in c.vehicles.all()
        ],
    })


@login_required
def api_lookup_vehicle(request):
    reg = request.GET.get("reg", "").strip().upper()
    if len(reg) < 4:
        return JsonResponse({"found": False})
    v = (
        Vehicle.objects.filter(registration_number=reg).first()
        or Vehicle.objects.filter(registration_number__startswith=reg).first()
        or Vehicle.objects.filter(registration_number__icontains=reg).first()
    )
    if not v:
        return JsonResponse({"found": False})
    return JsonResponse({
        "found": True, "id": v.id,
        "reg": v.registration_number, "make": v.make, "model": v.model,
        "type": v.vehicle_type, "color": v.color, "year": v.year, "odometer": v.odometer,
        "engine_number": v.engine_number, "chassis_number": v.chassis_number,
        "customer": {"id": v.customer.id, "name": v.customer.name, "phone": v.customer.phone,
                     "email": v.customer.email, "address": v.customer.address, "gstin": v.customer.gstin},
    })


@login_required
def list_customers(request):
    q = request.GET.get("q", "").strip()
    customers = Customer.objects.all().order_by("-created_at")
    if q:
        customers = customers.filter(Q(name__icontains=q) | Q(phone__icontains=q) | Q(email__icontains=q) | Q(vehicles__registration_number__icontains=q)).distinct()
    return render(request, "customers/list.html", {"customers": customers, "q": q})


@login_required
def quick_register(request):
    if request.method == "POST":
        form = QuickRegisterForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            customer, _ = Customer.objects.get_or_create(
                phone=d["phone"],
                defaults={"name": d["name"], "email": d.get("email", ""), "address": d.get("address", ""), "gstin": d.get("gstin", "")},
            )
            vehicle, _ = Vehicle.objects.get_or_create(
                registration_number=d["registration_number"].upper(),
                defaults={
                    "customer": customer,
                    "vehicle_type": d["vehicle_type"],
                    "make": d["make"],
                    "model": d["model"],
                    "engine_number": d.get("engine_number", ""),
                    "chassis_number": d.get("chassis_number", ""),
                    "color": d.get("color", ""),
                    "year": d.get("year"),
                    "odometer": d.get("odometer") or 0,
                },
            )
            changed = False
            if d.get("engine_number") and not vehicle.engine_number:
                vehicle.engine_number = d["engine_number"]
                changed = True
            if d.get("chassis_number") and not vehicle.chassis_number:
                vehicle.chassis_number = d["chassis_number"]
                changed = True
            if changed:
                vehicle.save(update_fields=["engine_number", "chassis_number"])
            jc = JobCard.objects.create(
                customer=customer,
                vehicle=vehicle,
                inspection_notes=d.get("inspection_notes", ""),
                odometer_in=d.get("odometer") or 0,
            )
            sent, reason = send_jobcard_created_whatsapp(jc)
            if sent:
                messages.success(request, "WhatsApp confirmation sent to customer.")
            messages.success(request, f"Customer registered and Job Card {jc.job_number} created.")
            return redirect("jobcards:setup", pk=jc.pk)
    else:
        form = QuickRegisterForm()
    return render(request, "customers/quick_register.html", {"form": form})


@login_required
def detail(request, pk):
    from datetime import date
    from billing.models import Invoice
    from reminders.models import Reminder

    customer = get_object_or_404(Customer, pk=pk)
    vehicles = customer.vehicles.all()
    jobcards = customer.jobcards.select_related("vehicle").order_by("-created_at")

    jc_list = []
    total_spend = 0
    for jc in jobcards:
        try:
            inv = jc.invoice
            amount = inv.total
            total_spend += amount
        except Exception:
            amount = None
        jc_list.append({"jc": jc, "amount": amount})

    reminders = (Reminder.objects
                 .filter(vehicle__customer=customer)
                 .select_related("vehicle")
                 .order_by("due_date")[:10])

    today = date.today()
    return render(request, "customers/detail.html", {
        "customer": customer,
        "vehicles": vehicles,
        "jc_list": jc_list,
        "total_spend": total_spend,
        "total_visits": len(jc_list),
        "reminders": reminders,
        "today": today,
    })


@login_required
def edit(request, pk):
    from billing.models import Invoice

    customer = get_object_or_404(Customer, pk=pk)
    if request.method == "POST":
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, "Customer info updated.")
            return redirect("customers:edit", pk=pk)
    else:
        form = CustomerForm(instance=customer)

    all_jobs = customer.jobcards.select_related("vehicle").order_by("-created_at")
    open_jobs = [j for j in all_jobs if j.status in ("open", "in_progress")]
    completed_raw = [j for j in all_jobs if j.status not in ("open", "in_progress")]
    completed_jobs = []
    for j in completed_raw:
        try:
            amount = j.invoice.total
        except Exception:
            amount = None
        completed_jobs.append({"jc": j, "amount": amount})

    latest_job = open_jobs[0] if open_jobs else (all_jobs.first())

    return render(request, "customers/edit.html", {
        "customer": customer,
        "cust_form": form,
        "vehicles": customer.vehicles.all(),
        "open_jobs": open_jobs,
        "completed_jobs": completed_jobs,
        "latest_job": latest_job,
    })


@login_required
def delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == "POST":
        try:
            customer.delete()
            messages.success(request, "Customer deleted.")
        except ProtectedError:
            messages.error(
                request,
                "Cannot delete this customer because related records exist (for example, job cards).",
            )
    return redirect("customers:list")


@login_required
def add_vehicle(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == "POST":
        form = VehicleForm(request.POST)
        if form.is_valid():
            v = form.save(commit=False)
            v.customer = customer
            v.registration_number = v.registration_number.upper()
            v.save()
            messages.success(request, "Vehicle added.")
            return redirect("customers:detail", pk=pk)
    else:
        form = VehicleForm()
    return render(request, "customers/vehicle_form.html", {"form": form, "title": f"Add Vehicle for {customer.name}"})


@login_required
def vehicle_detail(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    return render(request, "customers/vehicle_detail.html", {
        "vehicle": vehicle,
        "jobcards": vehicle.jobcards.all().order_by("-created_at"),
        "reminders": vehicle.reminders.all(),
    })


@login_required
def edit_vehicle(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    if request.method == "POST":
        form = VehicleForm(request.POST, instance=vehicle)
        if form.is_valid():
            form.save()
            messages.success(request, "Vehicle updated.")
            return redirect("customers:vehicle_detail", pk=pk)
    else:
        form = VehicleForm(instance=vehicle)
    return render(request, "customers/vehicle_form.html", {"form": form, "title": "Edit Vehicle"})


@login_required
def delete_vehicle(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    customer_pk = vehicle.customer.pk
    if request.method == "POST":
        try:
            vehicle.delete()
            messages.success(request, "Vehicle deleted.")
        except ProtectedError:
            messages.error(
                request,
                "Cannot delete this vehicle because service history/job cards exist.",
            )
    return redirect("customers:detail", pk=customer_pk)

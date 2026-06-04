from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models.deletion import ProtectedError
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from .forms import PartForm, SupplierForm, RestockForm
from .models import Part, Supplier, StockMovement


@login_required
def list_parts(request):
    q = request.GET.get("q", "").strip()
    parts = Part.objects.all().order_by("name")
    if q:
        parts = parts.filter(Q(sku__icontains=q) | Q(name__icontains=q) | Q(category__icontains=q))
    return render(request, "inventory/list.html", {"parts": parts, "q": q})


@login_required
def create_part(request):
    if request.method == "POST":
        form = PartForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Part added with QR code.")
            return redirect("inventory:list")
    else:
        form = PartForm()
    return render(request, "inventory/form.html", {"form": form, "title": "Add Part"})


@login_required
def detail(request, pk):
    part = get_object_or_404(Part, pk=pk)
    return render(request, "inventory/detail.html", {"part": part, "movements": part.movements.all()[:20]})


@login_required
def edit(request, pk):
    part = get_object_or_404(Part, pk=pk)
    if request.method == "POST":
        form = PartForm(request.POST, instance=part)
        if form.is_valid():
            form.save()
            return redirect("inventory:detail", pk=pk)
    else:
        form = PartForm(instance=part)
    return render(request, "inventory/form.html", {"form": form, "title": "Edit Part"})


@login_required
def delete(request, pk):
    part = get_object_or_404(Part, pk=pk)
    if request.method == "POST":
        try:
            part.delete()
            messages.success(request, "Part deleted.")
        except ProtectedError:
            messages.error(request, "Cannot delete this part because it is used in job cards.")
    return redirect("inventory:list")


@login_required
def restock(request, pk):
    part = get_object_or_404(Part, pk=pk)
    if request.method == "POST":
        form = RestockForm(request.POST)
        if form.is_valid():
            qty = form.cleaned_data["quantity"]
            part.stock += qty
            part.save()
            StockMovement.objects.create(part=part, movement_type="in", quantity=qty, note=form.cleaned_data.get("note", ""))
            messages.success(request, f"Added {qty} units to stock.")
            return redirect("inventory:detail", pk=pk)
    else:
        form = RestockForm()
    return render(request, "inventory/form.html", {"form": form, "title": f"Restock: {part.name}"})


@login_required
def scan(request):
    return render(request, "inventory/scan.html")


@login_required
def api_lookup(request):
    code = request.GET.get("code", "").strip()
    try:
        part = Part.objects.get(sku=code)
        return JsonResponse({
            "success": True,
            "id": part.id,
            "sku": part.sku,
            "name": part.name,
            "unit_price": str(part.unit_price),
            "stock": part.stock,
        })
    except Part.DoesNotExist:
        return JsonResponse({"success": False, "error": "Part not found"})


@login_required
def suppliers(request):
    if request.method == "POST":
        form = SupplierForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("inventory:suppliers")
    else:
        form = SupplierForm()
    return render(request, "inventory/suppliers.html", {"form": form, "suppliers": Supplier.objects.all()})

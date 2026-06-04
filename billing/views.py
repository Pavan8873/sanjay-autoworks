from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .forms import ManualChargeForm, PaymentForm, InvoiceEditForm
from .models import Invoice, ManualCharge


@login_required
def list_invoices(request):
    status = request.GET.get("status", "")
    invoices = Invoice.objects.select_related("jobcard__customer", "jobcard__vehicle").order_by("-created_at")
    if status == "paid":
        invoices = invoices.filter(paid=True)
    elif status == "pending":
        invoices = invoices.filter(paid=False)
    return render(request, "billing/list.html", {"invoices": invoices, "status": status})


@login_required
def detail(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    invoice.recalculate()
    return render(request, "billing/detail.html", {
        "invoice": invoice,
        "charge_form": ManualChargeForm(),
        "payment_form": PaymentForm(instance=invoice),
        "presets": ManualCharge.PRESETS,
    })


@login_required
def add_charge(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    form = ManualChargeForm(request.POST)
    if form.is_valid():
        c = form.save(commit=False)
        c.invoice = invoice
        c.save()
        invoice.recalculate()
        messages.success(request, "Charge added.")
    return redirect("billing:detail", pk=pk)


@login_required
def remove_charge(request, pk, charge_id):
    invoice = get_object_or_404(Invoice, pk=pk)
    ManualCharge.objects.filter(pk=charge_id, invoice=invoice).delete()
    invoice.recalculate()
    return redirect("billing:detail", pk=pk)


@login_required
def mark_paid(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    if request.method == "POST":
        form = PaymentForm(request.POST, instance=invoice)
        if form.is_valid():
            inv = form.save(commit=False)
            method = (inv.payment_method or "").strip().lower()
            inv.payment_method = method if method in {"cash", "upi", "card", "bank", "pending"} else "pending"
            inv.paid = inv.payment_method != "pending"
            inv.save()
            inv.jobcard.status = "billed" if inv.paid else "completed"
            inv.jobcard.save()
            if inv.paid:
                messages.success(request, "Payment recorded.")
            else:
                messages.info(request, "Invoice kept as pending.")
        else:
            messages.error(request, "Could not update payment status. Please select a valid payment method.")
    return redirect("billing:list")


@login_required
def print_invoice(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    invoice.recalculate()
    return render(request, "billing/print.html", {"invoice": invoice})


@login_required
def edit_invoice(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    if request.method == "POST":
        form = InvoiceEditForm(request.POST, instance=invoice)
        if form.is_valid():
            inv = form.save()
            inv.recalculate()
            if inv.paid:
                inv.jobcard.status = "billed"
            elif inv.jobcard.status == "billed":
                inv.jobcard.status = "completed"
            inv.jobcard.save(update_fields=["status"])
            messages.success(request, "Invoice updated.")
            return redirect("billing:detail", pk=inv.pk)
    else:
        form = InvoiceEditForm(instance=invoice)
    return render(request, "billing/form.html", {"form": form, "title": f"Edit {invoice.invoice_number}"})


@login_required
def delete_invoice(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    if request.method == "POST":
        job = invoice.jobcard
        invoice.delete()
        if job.status == "billed":
            job.status = "completed"
            job.save(update_fields=["status"])
        messages.success(request, "Invoice deleted.")
    return redirect("billing:list")

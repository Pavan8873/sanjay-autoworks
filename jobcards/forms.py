from django import forms
from .models import JobCard, JobCardPart, ServiceChecksheet, CS_ITEMS

WA_FIELDS = [
    ("wa_windshield", "Windshield glass"),
    ("wa_toolkit", "Tool kit"),
    ("wa_jack", "Jack & handle"),
    ("wa_spare_wheel", "Spare wheel"),
    ("wa_wheel_cap", "Wheel cap / Alloy wheel"),
    ("wa_audio", "Audio system"),
    ("wa_cd_pendrive", "CD/Pendrive"),
    ("wa_mat", "Mat"),
    ("wa_warranty_book", "Warranty book"),
    ("wa_idol", "Idol"),
    ("wa_perfume", "Perfume bottle"),
    ("wa_central_locking", "Central locking/Remote"),
    ("wa_steering", "Steering wheel/cover"),
]

CS_STATUS_CHOICES = [("", "—"), ("ok", "OK"), ("ng", "NG")]


class JobCardForm(forms.ModelForm):
    class Meta:
        model = JobCard
        fields = [
            "customer", "vehicle", "service_advisor", "mechanic",
            "odometer_in", "battery_condition", "tyres_condition",
            "inspection_notes", "work_to_do", "status",
            "wa_windshield", "wa_toolkit", "wa_jack", "wa_spare_wheel",
            "wa_wheel_cap", "wa_audio", "wa_cd_pendrive", "wa_mat",
            "wa_warranty_book", "wa_idol", "wa_perfume",
            "wa_central_locking", "wa_steering",
        ]
        widgets = {
            "wa_windshield": forms.RadioSelect,
            "wa_toolkit": forms.RadioSelect,
            "wa_jack": forms.RadioSelect,
            "wa_spare_wheel": forms.RadioSelect,
            "wa_wheel_cap": forms.RadioSelect,
            "wa_audio": forms.RadioSelect,
            "wa_cd_pendrive": forms.RadioSelect,
            "wa_mat": forms.RadioSelect,
            "wa_warranty_book": forms.RadioSelect,
            "wa_idol": forms.RadioSelect,
            "wa_perfume": forms.RadioSelect,
            "wa_central_locking": forms.RadioSelect,
            "wa_steering": forms.RadioSelect,
            "work_to_do": forms.Textarea(attrs={"rows": 4}),
            "inspection_notes": forms.Textarea(attrs={"rows": 3}),
        }


class AddPartForm(forms.Form):
    sku = forms.CharField(max_length=60, required=False, label="Scan / Enter SKU")
    part_id = forms.IntegerField(required=False, widget=forms.HiddenInput)
    quantity = forms.IntegerField(min_value=1, initial=1)


class ChecksheetForm(forms.Form):
    battery_voltage = forms.CharField(max_length=20, required=False, label="Battery Voltage (V)")
    battery_cell_1 = forms.CharField(max_length=20, required=False, label="Cell 1")
    battery_cell_2 = forms.CharField(max_length=20, required=False, label="Cell 2")
    battery_cell_3 = forms.CharField(max_length=20, required=False, label="Cell 3")
    battery_cell_4 = forms.CharField(max_length=20, required=False, label="Cell 4")
    battery_cell_5 = forms.CharField(max_length=20, required=False, label="Cell 5")
    battery_cell_6 = forms.CharField(max_length=20, required=False, label="Cell 6")
    brake_front_lhs = forms.CharField(max_length=20, required=False, label="Front LHS (mm)")
    brake_front_rhs = forms.CharField(max_length=20, required=False, label="Front RHS (mm)")
    brake_rear_lhs = forms.CharField(max_length=20, required=False, label="Rear LHS (mm)")
    brake_rear_rhs = forms.CharField(max_length=20, required=False, label="Rear RHS (mm)")
    brake_liners = forms.CharField(widget=forms.Textarea(attrs={"rows": 2}), required=False, label="Brake Liners")
    diagnostics_report = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), required=False, label="Diagnostics Report")
    job_remarks = forms.CharField(widget=forms.Textarea(attrs={"rows": 4}), required=False, label="Job Performed / Remarks / Findings")

    def __init__(self, *args, **kwargs):
        instance = kwargs.pop("instance", None)
        super().__init__(*args, **kwargs)
        existing_cl = {}
        if instance:
            for field in ("battery_voltage", "battery_cell_1", "battery_cell_2",
                          "battery_cell_3", "battery_cell_4", "battery_cell_5",
                          "battery_cell_6", "brake_front_lhs", "brake_front_rhs",
                          "brake_rear_lhs", "brake_rear_rhs", "brake_liners",
                          "diagnostics_report", "job_remarks"):
                self.fields[field].initial = getattr(instance, field, "")
            existing_cl = instance.checklist or {}
        for key, label in CS_ITEMS:
            item = existing_cl.get(key, {})
            self.fields[f"cs_{key}"] = forms.ChoiceField(
                choices=CS_STATUS_CHOICES,
                required=False,
                widget=forms.RadioSelect(attrs={"class": "cs-radio"}),
                label=label,
                initial=item.get("status", ""),
            )
            self.fields[f"cs_{key}_rem"] = forms.CharField(
                max_length=200, required=False, label="",
                initial=item.get("remarks", ""),
                widget=forms.TextInput(attrs={"placeholder": "Remarks"}),
            )

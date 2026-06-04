from django.contrib import admin
from .models import JobCard, JobCardPart, LabourCharge, ManualJobPart, ServiceChecksheet

admin.site.register(JobCard)
admin.site.register(JobCardPart)
admin.site.register(LabourCharge)
admin.site.register(ManualJobPart)
admin.site.register(ServiceChecksheet)

from django.contrib import admin
from .models import VerificationRequest,FreeTrial
# Register your models here.
admin.site.register(VerificationRequest)
admin.site.register(FreeTrial)
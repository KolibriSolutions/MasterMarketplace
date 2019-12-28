from django.contrib import admin
from .models import *

admin.site.register(UserLogin)
admin.site.register(ProjectStatusChange)
admin.site.register(ApplicationTracking)
admin.site.register(RegistrationTracking)
admin.site.register(TelemetryKey)
admin.site.register(DistributionTracking)
admin.site.register(ProjectTracking)
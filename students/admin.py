from django.contrib import admin

from .models import Application, Distribution


class ApplicationAdmin(admin.ModelAdmin):
    readonly_fields = ('Timestamp',)
    search_fields = ('Student__username', 'Student__last_name', 'Project__Title')


class DistributionAdmin(admin.ModelAdmin):
    search_fields = ('Student__username', 'Student__last_name', 'Project__Title')


admin.site.register(Application, ApplicationAdmin)
admin.site.register(Distribution, DistributionAdmin)

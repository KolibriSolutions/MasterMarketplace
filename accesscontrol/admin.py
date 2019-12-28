from django.contrib import admin

from .models import *


class AllowedAccessAdmin(admin.ModelAdmin):
    search_fields = ['User__username', 'Email']


admin.site.register(Origin)
admin.site.register(AllowedAccess, AllowedAccessAdmin)
admin.site.register(AccessGrantStaff)
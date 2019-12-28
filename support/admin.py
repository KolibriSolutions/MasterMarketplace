from django.contrib import admin

from .models import Promotion, MailTemplate, Mailing

admin.site.register(Promotion)
admin.site.register(MailTemplate)
admin.site.register(Mailing)

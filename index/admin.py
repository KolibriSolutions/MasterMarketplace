from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import Broadcast, FeedbackReport, UserMeta, Term, UserAcceptedTerms


class UserMetaAdmin(admin.ModelAdmin):
    search_fields = ['User__username', 'Fullname', 'User__email', 'User__username']
    list_filter = ('User__groups', 'Cohort')
    list_display = ['Fullname', 'User', 'user_link']

    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.User.id])
        return format_html("<a href='{}'>{}</a>", url, obj)


class UserAcceptedTermsAdmin(admin.ModelAdmin):
    search_fields = ['User__username']


admin.site.register(Term)
admin.site.register(UserAcceptedTerms, UserAcceptedTermsAdmin)
admin.site.register(UserMeta, UserMetaAdmin)
admin.site.register(Broadcast)
admin.site.register(FeedbackReport)

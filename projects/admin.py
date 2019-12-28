from django.contrib import admin

from .models import Project, ProjectImage, ProjectAttachment, Favorite, ProjectLabel
from django.shortcuts import reverse
from django.utils.html import format_html


class ProjectAdmin(admin.ModelAdmin):
    search_fields = ['Title', ]
    list_display = ['Title', 'ResponsibleStaff', 'Status', 'detail_link']
    list_filter = ('Type', 'Status', 'Group')

    def detail_link(self, obj):
        url = reverse('projects:details', args=[obj.id])
        return format_html("<a href='{}'>{}</a>", url, obj)


class ProjectFileAdmin(admin.ModelAdmin):
    search_fields = ['Project__Title', 'Caption']


class ProjectLabelAdmin(admin.ModelAdmin):
    search_fields = ['Name']
    list_display = ['Name', 'Active', 'display_color']
    list_filter = ['Active']

    def display_color(self, obj):
        return format_html('{} - ({})', obj.get_Color_display(), obj.Color)


class ProjectFavoriteAdmin(admin.ModelAdmin):
    search_fields = ['Project', 'User']
    list_display = ['__str__', 'detail_link', 'User']

    def detail_link(self, obj):
        url = reverse('projects:details', args=[obj.Project.id])
        return format_html("<a href='{}'>{}</a>", url, obj.Project)


admin.site.register(Project, ProjectAdmin)
admin.site.register(ProjectLabel, ProjectLabelAdmin)
admin.site.register(ProjectImage, ProjectFileAdmin)
admin.site.register(ProjectAttachment, ProjectFileAdmin)
admin.site.register(Favorite, ProjectFavoriteAdmin)

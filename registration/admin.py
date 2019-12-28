from django.contrib import admin

from .models import RegistrationDeadline, Registration, RegistrationDeadlineDescription, PlannedCourse, Planning


class PlannedCourseAdmin(admin.ModelAdmin):
    search_fields = ['Code', ]
    list_filter = ('Code', 'Year', 'Planning')


class RegistrationAdmin(admin.ModelAdmin):
    search_fields = ['Student__usermeta__Fullname']
    list_filter = ('Origin', 'Program')

admin.site.register(Registration, RegistrationAdmin)
admin.site.register(RegistrationDeadline)
admin.site.register(RegistrationDeadlineDescription)
admin.site.register(Planning)
admin.site.register(PlannedCourse, PlannedCourseAdmin)

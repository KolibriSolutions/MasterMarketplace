from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.forms import ValidationError
from django.utils.safestring import mark_safe

from general_model import clean_text, get_ext, print_list, filename_default
from registration.CourseBrowser import CourseBrowser
from timeline.models import Year
from timeline.utils import get_year_id


class CapacityGroup(models.Model):
    ShortName = models.CharField(max_length=3)
    FullName = models.CharField(max_length=256)
    Info = models.TextField(default='', blank=True)
    Administrators = models.ManyToManyField(User, related_name='administratorgroups',
                                            through='GroupAdministratorThrough')
    Head = models.ForeignKey(User, blank=True, null=True, on_delete=models.PROTECT, related_name='capacity_group_head')

    def __str__(self):
        return self.ShortName

    def clean(self):
        self.Info = clean_text(self.Info)
        self.FullName = clean_text(self.FullName)
        self.ShortName = clean_text(self.ShortName)


class CapacityGroupImage(models.Model):
    def make_upload_path(instance, filename):
        filename_new = filename_default(filename)
        return 'capacitygroup_{0}/{1}'.format(instance.CapacityGroup.pk, filename_new)

    CapacityGroup = models.ForeignKey(CapacityGroup, on_delete=models.CASCADE, related_name='images')
    File = models.ImageField(default=None, upload_to=make_upload_path)
    Caption = models.CharField(max_length=200, blank=True, null=True)
    OriginalName = models.CharField(max_length=200, blank=True, null=True)

    def save(self, *args, **kwargs):
        # remove old image if this is a changed image
        try:
            this_old = CapacityGroupImage.objects.get(id=self.id)
            if this_old.File != self.File:
                this_old.File.delete(save=False)
        except CapacityGroupImage.DoesNotExist:  # new image object
            pass
        super(CapacityGroupImage, self).save(*args, **kwargs)

    def clean(self):
        if self.File:
            if get_ext(self.File.name) not in settings.ALLOWED_PROJECT_IMAGES:
                raise ValidationError(
                    'This file type is not allowed. Allowed types: ' + print_list(settings.ALLOWED_PROJECT_IMAGES))

    def __str__(self):
        return '{} - {}'.format(self.CapacityGroup.ShortName, self.OriginalName)


class GroupAdministratorThrough(models.Model):
    """
    Through-model between User and CapacityGroup to store read/write access as groupadministrator
    Called via CapacityGroup.Administrators
    """
    Group = models.ForeignKey(CapacityGroup, on_delete=models.CASCADE)
    User = models.ForeignKey(User, on_delete=models.CASCADE, related_name='administratoredgroups')
    Super = models.BooleanField(default=False, blank=True)


class CourseType(models.Model):
    Name = models.CharField(max_length=64)

    def __str__(self):
        return self.Name


class MainCourse(models.Model):
    """
    This class represents a course selected by the study advisor to be in the studyguide.
    it will also be displayed in the course planner by default.
    please note that extra courses can be added by student to its planning, this model is for the courses that are offered by default
    this is only a mapping of course codes to their year and their types and making sure the studyguide is not cluttered
    """
    Code = models.CharField(max_length=6)
    Type = models.ForeignKey(CourseType, on_delete=models.CASCADE, related_name='courses')
    Year = models.ForeignKey(Year, on_delete=models.CASCADE, related_name='courses')

    def __str__(self):
        return "{} - {}".format(self.Code, self.Year)

    def Info(self):
        api = CourseBrowser(self.Year.Begin.year)
        info = api.get_course_data(self.Code)
        try:  # return first course
            return info[0]
        except:
            return None


class MasterProgram(models.Model):
    """
    A master program or specialization path. Track of courses of a capacity group
    """
    MainCourses = models.ManyToManyField(MainCourse, related_name='programs')
    Name = models.CharField(max_length=32)
    Group = models.ManyToManyField(CapacityGroup, related_name='programs')
    DetailLink = models.URLField(null=True, blank=True)
    Info = models.TextField(null=True, blank=True)
    Year = models.ForeignKey(Year, blank=False, null=False, on_delete=models.PROTECT, default=get_year_id)

    def __str__(self):
        return '{} in {}'.format(self.Name, self.Year)

    def get_link(self):
        return mark_safe("<a href=\"{}\" target=\"_blank\">{}</a>".format(self.DetailLink, self.__str__()))

    def clean(self):
        self.Info = clean_text(self.Info)
        self.Name = clean_text(self.Name)


class MasterProgramImage(models.Model):
    def make_upload_path(instance, filename):
        filename_new = filename_default(filename)
        return 'masterprogram_{0}/{1}'.format(instance.MasterProgram.pk, filename_new)

    MasterProgram = models.ForeignKey(MasterProgram, on_delete=models.CASCADE, related_name='images')
    File = models.ImageField(default=None, upload_to=make_upload_path)
    Caption = models.CharField(max_length=200, blank=True, null=True)
    OriginalName = models.CharField(max_length=200, blank=True, null=True)

    def save(self, *args, **kwargs):
        # remove old image if this is a changed image
        try:
            this_old = MasterProgramImage.objects.get(id=self.id)
            if this_old.File != self.File:
                this_old.File.delete(save=False)
        except MasterProgramImage.DoesNotExist:  # new image object
            pass
        super(MasterProgramImage, self).save(*args, **kwargs)

    def clean(self):
        if self.File:
            if get_ext(self.File.name) not in settings.ALLOWED_PROJECT_IMAGES:
                raise ValidationError(
                    'This file type is not allowed. Allowed types: ' + print_list(settings.ALLOWED_PROJECT_IMAGES))

    def __str__(self):
        return '{} - {}'.format(self.MasterProgram, self.OriginalName)


class MenuLink(models.Model):
    """
    A link to a custom location in the studyguide menu.
    For tue website studyguide and mentor list
    """
    Name = models.TextField(max_length=32)
    Url = models.URLField()
    Icon = models.TextField(max_length=32, blank=True, null=True, help_text='For instance "files-empty" or "heart" ')

    def __str__(self):
        return self.Name

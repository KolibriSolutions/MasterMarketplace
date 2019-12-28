import json

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db import utils
from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver
from django.forms import ValidationError

from general_model import clean_text
from general_model import file_delete_default
from general_model import filename_default, get_ext, print_list
from studyguide.models import CapacityGroup

try:
    from django.contrib.auth.models import Group

    # mailing list options
    # do not remove items, as they might be stored in mailtemplates.
    mail_student_options = (
        ('all', 'All students'),
        ('registered', 'Registered students'),
        ('not-registered', 'ELE students, logged in, not registered'),
        ('distributed', 'Students with assigned project'),
        ('not-logged-in', 'Students with access, not logged in'),
    )
    mail_staff_options = tuple(Group.objects.all().values_list('name', 'name'))
    mail_staff_options += (
        ('staffdraftproj', 'Staff with draft project'),
        ('distributedstaff', 'Staff with students'),
        ('staffnostudents', 'Staff with no students'),
    )
except utils.OperationalError:
    # happens during migrations
    mail_staff_options = ((), ())
    mail_student_options = ((), ())


class MailTemplate(models.Model):
    """
    Template for a mailing list mail
    """
    RecipientsStudents = models.CharField(max_length=400)
    RecipientsStaff = models.CharField(max_length=400)
    Subject = models.CharField(max_length=400)
    Message = models.TextField()
    TimeStamp = models.DateTimeField(auto_now=True, null=True)
    Created = models.DateTimeField(auto_now_add=True, null=True)

    def RecipientsStudentsList(self):
        return [dict(mail_student_options).get(a) for a in json.loads(self.RecipientsStudents)]

    def RecipientsStaffList(self):
        return [dict(mail_staff_options).get(a) for a in json.loads(self.RecipientsStaff)]

    def __str__(self):
        return '{} at {}'.format(self.Subject, self.TimeStamp)


class Mailing(models.Model):
    """
    A mailing sent using the system.
    """
    RecipientsStaff = models.ManyToManyField(User, related_name='received_mailings_staff', default=None, blank=True)
    RecipientsStudents = models.ManyToManyField(User, related_name='received_mailings_students', default=None, blank=True)
    Subject = models.CharField(max_length=400)
    Message = models.TextField()
    Sent = models.BooleanField(default=False)
    TimeStamp = models.DateTimeField(auto_now=True, null=True)
    Created = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return '{} at {} (sent:{})'.format(self.Subject, self.TimeStamp, self.Sent)


class Promotion(models.Model):
    """
    A promotional text in the sidebar
    """

    def make_upload_path(instance, filename):
        filename_new = filename_default(filename)
        return 'promotion/{}'.format(filename_new)

    Organization = models.CharField(max_length=15)
    Text = models.CharField(max_length=512)
    File = models.ImageField(default=None, blank=True, null=True, upload_to=make_upload_path)
    CapacityGroups = models.ManyToManyField(CapacityGroup, related_name='promotions', default=None, blank=True)
    Visible = models.BooleanField(default=True)
    Url = models.URLField(default=None, blank=True, null=True)

    def __str__(self):
        return self.Organization

    def save(self, *args, **kwargs):
        # remove old image if this is a changed image
        try:
            this_old = Promotion.objects.get(id=self.id)
            if this_old.File != self.File:
                this_old.File.delete(save=False)
        except:  # new image object
            pass
        super(Promotion, self).save(*args, **kwargs)

    def clean(self):
        self.Text = clean_text(self.Text)
        self.Organization = clean_text(self.Organization)

        if self.File:
            if get_ext(self.File.name) not in settings.ALLOWED_PROMOTION_LOGOS:
                raise ValidationError(
                    'This file type is not allowed. Allowed types: ' + print_list(settings.ALLOWED_PROMOTION_LOGOS))


@receiver(pre_delete, sender=Promotion)
def promotion_file_delete(sender, instance, **kwargs):
    """
    Delete actual file if publicfile Object is removed

    :param sender:
    :param instance:
    :param kwargs:
    :return:
    """
    file_delete_default(sender, instance)

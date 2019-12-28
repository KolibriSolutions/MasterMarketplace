import hmac
from datetime import date
from hashlib import sha256
from os import urandom

from django.contrib.auth.models import User
from django.db import models
from django.utils.timezone import localtime

from general_model import clean_text
from projects.models import Project


class UserLogin(models.Model):
    Subject = models.ForeignKey(User, on_delete=models.CASCADE, related_name='logins')
    Timestamp = models.DateTimeField(auto_now_add=True)
    Twofactor = models.BooleanField(default=False)

    def __str__(self):
        return self.Subject.usermeta.get_nice_name() + "@" + localtime(self.Timestamp).strftime("%H:%M %d-%m-%Y")


class ProjectStatusChange(models.Model):
    Subject = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="StatusChangeTracking")
    Timestamp = models.DateTimeField(auto_now_add=True)
    Actor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="StatusChangeTracking")
    StatusFrom = models.CharField(max_length=16, choices=Project.StatusOptions)
    StatusTo = models.CharField(max_length=16, choices=Project.StatusOptions)
    Message = models.CharField(max_length=500, null=True, blank=True)

    def clean(self):
        self.Message = clean_text(self.Message)


class ProjectTracking(models.Model):
    Subject = models.OneToOneField(Project, on_delete=models.CASCADE, related_name='tracking')
    UniqueVisitors = models.ManyToManyField(User, blank=True)

    def __str__(self):
        return str(self.Subject)


class ApplicationTracking(models.Model):
    typechoices = (
        ('a', 'applied'),
        ('r', 'retracted'),
    )

    Project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='applicationtrackings')
    Student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applicationtrackings')
    Timestamp = models.DateTimeField(auto_now_add=True)
    Type = models.CharField(max_length=1, choices=typechoices)


class DistributionTracking(models.Model):
    typechoices = (
        ('d', 'distributed'),
        ('u', 'undistributed'),
    )

    Project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='distributiontrackings')
    Student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='distributiontrackings')
    Timestamp = models.DateTimeField(auto_now_add=True)
    Type = models.CharField(max_length=1, choices=typechoices)


class RegistrationTracking(models.Model):
    TimeStamp = models.DateTimeField(auto_now_add=True)
    Student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='registrationtrackings')


def generate_key(length=64):
    return hmac.new(urandom(length), digestmod=sha256).hexdigest()


class TelemetryKey(models.Model):
    Created = models.DateTimeField(auto_now_add=True)
    ValidUntil = models.DateField(blank=True, null=True)
    Key = models.CharField(max_length=64, unique=True, default=generate_key)

    def is_valid(self):
        if self.ValidUntil is None:
            return True
        else:
            return date.today() <= self.ValidUntil

    def __str__(self):
        return 'Telemetry Access Key {}'.format(self.id)

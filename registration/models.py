from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Max

from general_model import clean_text
from studyguide.models import MasterProgram
from tracking.models import RegistrationTracking

class Registration(models.Model):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    OriginChoices = (
        ("bsc_ee_tue", "BSc EE TU/e"),  # Institute never needed
        ("bsc_au_tue", "BSc AU TU/e"),  # Institute never needed
        ("bsc_ele_other", "BSc EE Other"),  # Institute needed
        ("sense", "SENSE (Smart Electrical Networks and Systems)"),  # Institute may be filled in.
        ("premaster_hbo_tue", "Premaster HBO TU/e"),  # Institute may be filled in
        ("premaster_other", "Premaster Other"),  # Institute needed
        ("other", "Other institute"),  # Institute needed
    )

    StateChoices = (
        (1, "Student filling in"),
        (2, "Submitted for approval"),
        (3, "Approved")
    )

    Student = models.OneToOneField(User, related_name='registration', on_delete=models.CASCADE, blank=True)
    Cohort = models.IntegerField(validators=[
        MinValueValidator(2000),
        MaxValueValidator(2100)
    ], blank=True)
    Origin = models.CharField(max_length=32, choices=OriginChoices)
    Institute = models.CharField(max_length=256, blank=True, null=True)
    Program = models.ForeignKey(MasterProgram, on_delete=models.PROTECT, related_name='registrations')
    OutOfFacultyCourses = models.TextField(blank=True, null=True)  # TODO DEPRECATED
    State = models.IntegerField(choices=StateChoices, default=1)  # set default to allow form saving.

    def Approved(self):
        return self.State == 3

    def clean(self):
        self.Institute = clean_text(self.Institute)
        # self.OutOfFacultyCourses = clean_text(self.OutOfFacultyCourses)
        # self.OutOfFacultyCourses = self.OutOfFacultyCourses.replace(';', ',')
        if self.Origin in ['other', 'premaster_other']:  # Always institute needed
            if not self.Institute:
                raise ValidationError("Please specify your Institute")
        elif self.Origin in ['bsc_ee_tue', 'bsc_au_tue']:  # never Institute needed
            if self.Institute:
                raise ValidationError("Please leave the Institute field empty when Origin is TU/e")

    def __str__(self):
        return self.Student.usermeta.get_nice_name()

    def latestChange(self):
        try:
            return RegistrationTracking.objects.filter(Student=self.Student).aggregate(max=Max('TimeStamp'))['max']
        except:
            return None


class Planning(models.Model):
    Registration = models.OneToOneField(Registration, related_name='courseplanning', on_delete=models.CASCADE)
    Years = models.IntegerField(validators=[MinValueValidator(2)], default=2)

    def __str__(self):
        return "Planning of {}".format(self.Registration.Student)

    def get_course_codes(self):
        return set([c.Code for c in self.courses.all()])


class PlannedCourse(models.Model):
    """
    A course planned in a courseplanning
    """
    Code = models.CharField(max_length=16)
    Year = models.IntegerField(validators=[MinValueValidator(1)])
    Quartile = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(4)])
    Planning = models.ForeignKey(Planning, related_name='courses', on_delete=models.CASCADE)

    def __str__(self):
        return '{} for {} in Y{}Q{}'.format(self.Code, self.Planning, self.Year, self.Quartile)


class RegistrationDeadline(models.Model):
    types = (
        (1, 'First'),
        (2, 'Second')
    )
    Stamp = models.DateField()
    Type = models.IntegerField(unique=True, choices=types, validators=[MinValueValidator(1), MaxValueValidator(2)])

    def __str__(self):
        return 'type {} - {}'.format(self.Type, self.Stamp)


class RegistrationDeadlineDescription(models.Model):
    Title = models.CharField(max_length=100)
    Description = models.TextField()

    def clean(self):
        self.Title = clean_text(self.Title)
        self.Description = clean_text(self.Description)

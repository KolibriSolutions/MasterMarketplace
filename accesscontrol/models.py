# from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.auth.models import User
from django.db import models

from general_model import clean_text
from studyguide.models import CapacityGroup


class Origin(models.Model):
    Name = models.CharField(max_length=256, unique=True, help_text='Name of the origin. Name ELE is reserved.')
    Groups = models.ManyToManyField(CapacityGroup, help_text='Students of this origin can view projects of the selected capacity groups.')

    def __str__(self):
        return self.Name

    def clean(self):
        self.Name = clean_text(self.Name)


class AllowedAccess(models.Model):
    """
    Only type 0 (student) is used. The other ones are deprecated.
    for students
    """
    # types = (
    #     (0, 'students'),
    #     (1, 'studyadvisors'),
    #     (2, 'supervisors'),
    #     (3, 'assistants')
    # )

    # Type = models.IntegerField(choices=types, default=0) # deprecated field
    Email = models.EmailField(unique=True)
    # Origin = models.ForeignKey(Origin, default='ELE', to_field='Name', on_delete=models.CASCADE, related_name='students')  # postgres does not allow changing foreignkey :(
    Origin = models.ForeignKey(Origin, default=1, on_delete=models.PROTECT,
                               related_name='students')  # WARNING origin 1 should be ELE
    Cohort = models.IntegerField(null=True, blank=True)
    User = models.OneToOneField(User, blank=True, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return "{} from {}".format(self.Email, self.Origin)

    def clean(self):
        self.Email = clean_text(self.Email).lower().strip()


## for staff
class AccessGrantStaff(models.Model):
    LevelOptions = (
        (1, 'SuperVisor'),
        (2, 'Assistants')
    )

    Email = models.EmailField()
    Level = models.IntegerField(choices=LevelOptions, default=1)

    def __str__(self):
        return "{} for level {}".format(self.Email, self.Level)

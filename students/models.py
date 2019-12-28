from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models.signals import pre_delete
from django.db import models
from django.dispatch.dispatcher import receiver

from general_model import clean_text, get_ext, file_delete_default, metro_icon_default, filename_default, print_list
from projects.models import Project


class Application(models.Model):
    """
    A student's application to a project.
    """
    # Priority = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(settings.MAX_NUM_APPLICATIONS)])
    Project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='applications')
    Student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    Timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.Student.get_username() + " to " + self.Project.__str__()

    class Meta:
        ordering = ["Student"]

    def clean(self):
        if self.Student.applications.filter(Project=self.Project).exists():
            raise ValidationError("You already applied to this project")


class Distribution(models.Model):
    """A student distributed to a project"""
    Project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='distributions')
    Student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='distributions')
    Application = models.OneToOneField(Application, on_delete=models.SET_NULL, blank=True, null=True, related_name='distributions')

    def __str__(self):
        return self.Project.Title + " to " + self.Student.usermeta.get_nice_name() + " (" + self.Student.username + ")"

    def clean(self):
        if self.Student.distributions.filter(Project=self.Project).exists():
            raise ValidationError("You are already distributed to this project. "
                                  "(Changing this distribution is not allowed)")

    class Meta:
        ordering = ['Student']

    def save(self, *args, **kwargs):
        if self.Student.applications.exists():
            if self.Student.applications.filter(Project=self.Project).exists():
                appl = self.Student.applications.get(Project=self.Project)
            else:
                appl = None
        else:
            appl = None
        self.Application = appl
        super(Distribution, self).save(*args, **kwargs)


class FileExtension(models.Model):
    Name = models.CharField(max_length=256)

    def __str__(self):
        return self.Name

    def clean(self):
        if self.Name[0] == '.':
            raise ValidationError("Please give extension without dot.")


class StudentFile(models.Model):
    """
    Model for a file that a student uploads. Linked to a distribution.
    """

    def make_upload_path(instance, filename):
        filenameNew = filename_default(filename)
        return 'dist_{0}/{1}'.format(instance.Distribution.pk, filenameNew)

    Caption = models.CharField(max_length=200, blank=True, null=True)
    OriginalName = models.CharField(max_length=200, blank=True, null=True)
    File = models.FileField(default=None, upload_to=make_upload_path)
    Distribution = models.ForeignKey(Distribution, on_delete=models.CASCADE, related_name='files')
    # Type = models.ForeignKey(FileType, on_delete=models.CASCADE, related_name='files')
    TimeStamp = models.DateTimeField(auto_now=True)
    Created = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    def __str__(self):
        return self.OriginalName + " - " + self.Caption

    def metro_icon(self):
        return metro_icon_default(self)

    def save(self, *args, **kwargs):
        # remove old image if this is a changed image
        try:
            this_old = StudentFile.objects.get(id=self.id)
            if this_old.File != self.File:
                this_old.File.delete(save=False)
        except:  # new image object
            pass
        super(StudentFile, self).save(*args, **kwargs)

    def clean(self):
        self.Caption = clean_text(self.Caption)
        if self.File:
            if get_ext(self.File.name) not in FileExtension.objects.all().values_list('Name', flat=True):
                raise ValidationError(
                    'This file type is not allowed. Allowed types: '
                    + print_list(FileExtension.objects.all().values_list('Name', flat=True)))


@receiver(pre_delete, sender=StudentFile)
def student_file_delete(sender, instance, **kwargs):
    """
    Listener on studentfile, to remove the actual file when the object of the file is deleted.

    :param sender:
    :param instance:
    :param kwargs:
    :return:
    """
    file_delete_default(sender, instance)

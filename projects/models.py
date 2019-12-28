# from channels import Channel
import logging
import re
from datetime import datetime
from hashlib import sha256

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.core.validators import URLValidator
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver
from django.utils.html import escape

from general_model import file_delete_default, filename_default, clean_text, get_ext, print_list
from studyguide.models import CapacityGroup, MasterProgram, MainCourse

logger = logging.getLogger('django')
email_regex = re.compile(settings.EMAILREGEXCHECK)
link_regex = re.compile(settings.LINKREGEX)


class ProjectLabel(models.Model):
    """
    Label to categorize projects
    """
    ColorChoices = (
        ("bg-lime", "lime"),
        ("bg-green", "green"),
        ("bg-emerald", "emerald"),
        ("bg-teal", "teal"),
        ("bg-blue", "blue"),
        ("bg-cobalt", "cobalt"),
        ("bg-indigo", "indigo"),
        ("bg-violet", "violet"),
        ("bg-magenta", "magenta"),
        ("bg-crimson", "crimson"),
        ("bg-red", "red"),
        ("bg-orange", "orange"),
        ("bg-amber", "amber"),
        ("bg-yellow", "yellow"),
        ("bg-brown", "brown"),
        ("bg-olive", "olive"),
        ("bg-steel", "steel"),
        ("bg-mauve", "mauve"),
        ("bg-taupe", "taupe"),
        ("bg-gray", "gray"),
        # backup colors, if many labels are needed.
        # ("bg-darkOrange", "darkOrange"),
        # ("bg-darkCrimson", "darkCrimson"),
        # ("bg-darkGreen", "darkGreen"),
        # ("bg-darkEmerald", "darkEmerald"),
        # ("bg-darker", "darker"),
        # ("bg-darkCyan", "darkCyan"),
        # ("bg-darkCobalt", "darkCobalt"),
        # ("bg-darkPink", "darkPink"),
        # ("bg-darkViolet", "darkViolet"),
        # ("bg-darkBlue", "darkBlue"),
        # ("bg-lightBlue", "lightBlue"),
    )
    Name = models.CharField(max_length=50, unique=True)
    Color = models.CharField(max_length=20, choices=ColorChoices)
    Active = models.BooleanField(default=False)

    def clean(self):
        self.Name = clean_text(self.Name)
        # Remove ':' because it is used in string function.
        self.name = self.name.replace(':', '_')

    def __str__(self):
        """
        This format is used by select2 to display the color on the label form.

        :return:
        """
        return '{}:{}'.format(self.Name, self.Color)


class Project(models.Model):
    """
    Model for a project.
    """
    StatusOptions = (
        (1, "Draft, awaiting completion by assistant"),
        (2, "Draft, awaiting approval by responsible staff"),
        (3, "Active project"),
    )

    ApplyOptions = (
        ('system', 'Using master marketplace'),
        ('supervisor', 'By contacting supervisor'),
    )
    ProgressOptions = (
        (1, 'Project is being executed'),
        (2, 'Project is finished'),
        (3, 'Project is reserved'),
    )
    TypeOptions = (
        ('graduation', 'Graduation project'),
        ('internship', 'Internship project'),
        ('both', 'Graduation or internship project'),
    )
    Title = models.CharField(max_length=100)
    ResponsibleStaff = models.ForeignKey(User, on_delete=models.PROTECT, related_name='projectsresponsible')
    Assistants = models.ManyToManyField(User, related_name='projects', blank=True)
    ExternalStaff = models.TextField(blank=True, null=True, help_text='External staff (for instance company contact person). Please put one name and/or email on each line.')
    Group = models.ForeignKey(CapacityGroup, on_delete=models.PROTECT)
    SecondaryGroup = models.ManyToManyField(CapacityGroup, blank=True, related_name='secondarygroupprojects', help_text='One or more secondary capacity groups. Use if a project is shared with multiple capacity groups.')
    NumStudentsMin = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(10)])
    NumStudentsMax = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(10)])
    GeneralDescription = models.TextField(
        help_text='General description of the project. Hyperlinks will be tested before publishing.')
    StudentsTaskDescription = models.TextField(
        help_text='Task description of the project. Hyperlinks will be tested before publishing.')
    SiteUrl = models.URLField(blank=True, null=True,
                              help_text='Link to site of the group or other place with more information')
    Status = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(3)],
                                 choices=StatusOptions)
    Progress = models.IntegerField(default=None, blank=True, null=True, choices=ProgressOptions)
    StartDate = models.DateField(blank=True, null=True,
                                 help_text='Set this to the date from when students can view this project. Including this date.')
    EndDate = models.DateField(blank=True, null=True,
                               help_text='Set this to the date till when students can view this project. Visible including this date.')

    Type = models.CharField(default='graduation', max_length=16, choices=TypeOptions,
                            help_text="Choose the type of this project, like internship or graduation.")
    Apply = models.CharField(default='system', max_length=16, choices=ApplyOptions,
                             help_text="Choose whether students can apply to this project using an 'apply' button on the master marketplace or only by directly contacting the supervisor")
    Program = models.ManyToManyField(MasterProgram, related_name='restrictedprojects', blank=True,
                                     help_text='Required specialization path(s) to do this project.')
    RecommendedCourses = models.ManyToManyField(MainCourse, related_name='projects', blank=True,
                                                help_text='Courses recommended to be able to do this project. Leave the field blank if there are no recommended courses.')
    Labels = models.ManyToManyField(ProjectLabel, blank=True, related_name='projects', help_text='Assign category labels to this project.')
    TimeStamp = models.DateTimeField(auto_now=True, null=True)
    Created = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        try:
            return '{} from {}'.format(self.Title, self.ResponsibleStaff.usermeta.get_nice_name())
        except:
            return '{} from {}'.format(self.Title, self.ResponsibleStaff.username)

    def num_distributions(self):
        return int(self.distributions.count())

    def test_links(self):
        val = URLValidator()
        channel_layer = get_channel_layer()
        for text in [self.GeneralDescription, self.StudentsTaskDescription]:
            emailreg = re.compile(settings.EMAILREGEXCHECK)
            links = list(link_regex.finditer(text))
            for result in links:
                logger.info('model checks {}'.format(result.group(2)))
                if 'mailto' == result.group(2).split(':')[0]:
                    try:
                        if not emailreg.fullmatch(result.group(2).split(':')[1]):
                            logger.warning('Invalid email: {}'.format(result.group(2)))
                    except:
                        logger.warning('Invalid email: {}'.format(result.group(2)))
                    continue

                try:
                    val(result.group(2))
                except ValidationError:
                    continue
                h = sha256(result.group(2).encode()).hexdigest()
                cache.set('virustotal:owner:' + h, self.ResponsibleStaff.email, None)
                async_to_sync(channel_layer.send)(
                    'virustotal', {
                        'type': 'checklink',
                        'link': result.group(2)
                    }
                )
                # Channel('virustotal.checklink').send({
                #     "link": result.group(2),
                # })

    def clean(self):
        self.Title = clean_text(self.Title)
        self.GeneralDescription = clean_text(self.GeneralDescription)
        self.StudentsTaskDescription = clean_text(self.StudentsTaskDescription)
        self.ExternalStaff = escape(clean_text(self.ExternalStaff))
        self.test_links()

        if self.Status != 3 and self.Progress:
            raise ValidationError("Project being executed or finished needs to have status 3 (active)")

        if self.StartDate:
            if self.Progress and self.StartDate >= datetime.now().date():
                raise ValidationError("Project progress cannot be set on not-yet started projects.")
            if self.EndDate:
                if self.StartDate >= self.EndDate:
                    raise ValidationError("Start date cannot be later or the same as end date visible.")

        min_std = self.NumStudentsMin
        max_std = self.NumStudentsMax
        if min_std and max_std:
            if min_std > max_std:
                raise ValidationError("Minimum number of students cannot be higher than maximum.")
        else:
            raise ValidationError("Min or max number of students cannot be empty")

    def public_visible(self):
        if self.Status == 3:
            if self.StartDate:
                if self.StartDate > datetime.now().date():
                    return False
            if self.EndDate:
                if self.EndDate < datetime.now().date():
                    return False
            return True
        else:
            return False

    def ExternalStaffList(self):
        """
        Return each line of externallstaff as list with email address as link.

        :return: list of externalstaff
        """
        lst = []
        for es in self.ExternalStaff.split('\n'):  # each external staff
            tx = ''
            for part in es.split(' '):  # each word
                part = part.strip()
                if email_regex.match(part):  # if email address
                    tx += '<a href="mailto:{}">{}</a> '.format(part, part)
                else:
                    tx += part + ' '
            lst.append(tx)
        return lst


class ProjectFile(models.Model):
    """
    Abstract base class for any object attached to a project. Used for images and attachments.
    """

    def make_upload_path(instance, filename):
        filename_new = filename_default(filename)
        return 'project_{0}/{1}'.format(instance.Project.pk, filename_new)

    Caption = models.CharField(max_length=200, blank=True, null=True)
    OriginalName = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.Project.Title + ' ' + self.Caption

    def clean(self):
        self.Caption = clean_text(self.Caption)


class ProjectImage(ProjectFile):
    Project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='images')
    File = models.ImageField(default=None, upload_to=ProjectFile.make_upload_path)

    def save(self, *args, **kwargs):
        # remove old image if this is a changed image
        try:
            this_old = ProjectImage.objects.get(id=self.id)
            if this_old.File != self.File:
                this_old.File.delete(save=False)
        except ProjectImage.DoesNotExist:  # new image object
            pass
        super(ProjectImage, self).save(*args, **kwargs)

    def clean(self):
        if self.File:
            if get_ext(self.File.name) not in settings.ALLOWED_PROJECT_IMAGES:
                raise ValidationError(
                    'This file type is not allowed. Allowed types: ' + print_list(settings.ALLOWED_PROJECT_IMAGES))


class ProjectAttachment(ProjectFile):
    Project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='attachments')
    File = models.FileField(default=None, upload_to=ProjectFile.make_upload_path)

    def save(self, *args, **kwargs):
        # remove old attachement if the attachement changed
        try:
            this_old = ProjectAttachment.objects.get(id=self.id)
            if this_old.File != self.File:
                this_old.File.delete(save=False)
        except ProjectAttachment.DoesNotExist:  # new file object
            pass
        super(ProjectAttachment, self).save(*args, **kwargs)

    def clean(self):
        if self.File:
            if get_ext(self.File.name) not in settings.ALLOWED_PROJECT_ATTACHMENTS:
                raise ValidationError(
                    'This file type is not allowed. Allowed types: '
                    + print_list(settings.ALLOWED_PROJECT_ATTACHMENTS))


class Favorite(models.Model):
    """
    users favorite a project.
    """
    Project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='favorites')
    User = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    Timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return '{} to {}'.format(self.user.usermeta.get_nice_name(), self.Project)

    def clean(self):
        if self.User.favorites.filter(Project=self.Project).exists():
            raise ValidationError("You already favorite this project")


# delete image if ProjectImage Object is removed
@receiver(pre_delete, sender=[ProjectAttachment, ProjectImage])
def project_file_delete(sender, instance, **kwargs):
    file_delete_default(sender, instance)

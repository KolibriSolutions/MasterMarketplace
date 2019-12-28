import logging
import re

from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import MultipleObjectsReturned
from django.core.files.base import ContentFile
from django.core.files.images import get_image_dimensions
from django.forms import ValidationError

from MasterMarketplace.utils import get_user
from general_form import clean_file_default, FileForm
from general_mail import mail_project_single
from general_model import get_ext, print_list
from general_view import get_grouptype
from index.models import UserMeta
from templates import widgets
from tracking.models import ProjectStatusChange
from timeline.utils import get_year
from .models import ProjectImage, ProjectAttachment, Project, ProjectFile, ProjectLabel
from .utils import get_writable_admingroups
from studyguide.models import MainCourse

logger = logging.getLogger('django')

email_regex = re.compile(settings.EMAILREGEXCHECK)

# minimal image dimensions in px
minw = 30
minh = 30


def clean_image_default(self):
    """
    Check whether an uploaded image is valid and has right dimensions

    :param self:
    :return:
    """
    picture = clean_file_default(self)

    # this check is done both here and in the model, needed to prevent wrong files entering get_image_dimensions()
    if get_ext(picture.name) not in settings.ALLOWED_PROJECT_IMAGES:
        raise ValidationError('This file type is not allowed. Allowed types: '
                              + print_list(settings.ALLOWED_PROJECT_IMAGES))

    w, h = get_image_dimensions(picture)
    if w < minw or h < minh:
        raise ValidationError(
            "The image is too small, it has to be at least " + str(minw) + "px by " + str(
                minh) + "px and is only " + str(
                w) + "px by " + str(
                h) + "px.")

    return picture


def clean_attachment_default(self):
    """
    Check whether an attachment is valid

    :param self:
    :return:
    """
    file = clean_file_default(self)
    # this check is done both here and in the model
    if get_ext(file.name) not in settings.ALLOWED_PROJECT_ATTACHMENTS:
        raise ValidationError('This file type is not allowed. Allowed types: '
                              + print_list(settings.ALLOWED_PROJECT_ATTACHMENTS))
    return file


def clean_email_default(email, allowed_domains):
    """
    Clean email address and check if it has allowed domain

    :param email: emailadress in string
    :param allowed_domains: FQDN of allowed domain of mail
    :return: cleaned lowercase email addresss string or ValidationError
    """
    email = email.strip('\r').strip().lower()
    if not email_regex.match(email):
        raise forms.ValidationError(
            "Invalid email address ({}): Every line should contain one valid email address".format(email))
    # check if the domain is allowed (for instance @tue.nl )
    domain = email.split('@')[1]
    if domain not in allowed_domains:
        raise forms.ValidationError("This email domain is not allowed. Allowed domains: {}".
                                    format(print_list(allowed_domains)))
    return email


def get_or_create_user_email(email, student):
    """
    Get or create a user account

    :param email: emailaddress of the user to find
    :param student: whether the user is a student
    :return: a useraccount, either an existing or a newly created account
    """
    # temporary username till first login of user.
    username = email.split('@')[0].replace('.', '')
    try:
        account = get_user(email, username)  # check account match on email. If not exists check on username.
    except MultipleObjectsReturned:
        logger.error(
            "The user with email {} was added as assistant via emailaddress and has multiple accounts. One account should be removed.".format(
                email))
        return None

    if account:
        return account
    else:
        new_account = create_user_from_email(email, username, student)
        return new_account


def create_user_from_email(email, username, student=False):
    """
    Create a new user based on its email address.
    This user is updated with a real username as soon as the person logs in for the first time.

    :param email: emailaddres
    :param username: username to create, usually a part of the email address
    :param student: whether the users is a student. If false, user is added to the assistants group
    :return: THe created user account
    """
    parts = email.split('@')[0].split('.')
    # strip possible index number at the end.
    if parts[-1].isdigit():
        parts.pop()
    # get all single letters (initials etc)
    initials = ''
    while len(parts[0]) == 1:
        initials += parts.pop(0) + '.'
    # what remains is lastname. Join possible multiple last names.
    last_name = (' '.join(parts)).title()
    initials = initials.title()
    new_account = User.objects.create_user(username, email)
    new_account.first_name = initials
    new_account.last_name = last_name
    if not student:
        new_account.groups.add(get_grouptype("unverified"))
    new_account.full_clean()
    new_account.save()
    m = UserMeta(
        User=new_account,
        Initials=initials,
        Fullname="{}, {}".format(last_name, initials),
    )
    m.full_clean()
    m.save()
    return new_account


class ProjectForm(forms.ModelForm):
    """
    Form to create a project.
    """
    addAssistantsEmail = forms.CharField(label='Extra assistants (email, one per line)',
                                         widget=widgets.MetroMultiTextInput,
                                         required=False,
                                         help_text='Add an assistant using email address. Use this when the assistant cannot be found in the list of assistants')

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        self.fields['ResponsibleStaff'].queryset = get_grouptype("supervisors").user_set.all()
        self.fields['Assistants'].queryset = get_grouptype("assistants").user_set.all() | \
                                             get_grouptype("unverified").user_set.all() | \
                                             get_grouptype("supervisors").user_set.all()
        self.fields['ResponsibleStaff'].label_from_instance = self.user_label_from_instance
        self.fields['Assistants'].label_from_instance = self.user_label_from_instance
        self.fields['RecommendedCourses'].queryset = MainCourse.objects.filter(Year__Begin__gte=get_year().Begin)  # shows only courses from this year or newer.
        self.fields['RecommendedCourses'].label_from_instance = self.maincourse_label_from_instance
        self.fields['addAssistantsEmail'].widget.attrs['placeholder'] = "Add assistant via email address"
        self.fields['Labels'].queryset = ProjectLabel.objects.filter(Active=True)
        # self.fields['ExternalStaff'].queryset = get_grouptype("external").user_set.all()

    @staticmethod
    def user_label_from_instance(self):
        return self.usermeta.get_nice_name

    @staticmethod
    def maincourse_label_from_instance(self):
        try:
            return '{} - {}'.format(self.Code, self.Info()['name'])
        except:  # self.Info returns none if code not known in coursebrowser.
            return '{}'.format(self.Code)

    class Meta:
        model = Project
        fields = ['Title',
                  'ResponsibleStaff',
                  'Assistants',
                  'addAssistantsEmail',
                  'Group',
                  'SecondaryGroup',
                  'ExternalStaff',
                  'NumStudentsMin',
                  'NumStudentsMax',
                  'GeneralDescription',
                  'StudentsTaskDescription',
                  'SiteUrl',
                  'StartDate',
                  'EndDate',
                  'Type',
                  'Apply',
                  'Program',
                  'RecommendedCourses',
                  'Labels',
                  ]

        labels = {
            'ResponsibleStaff': "Responsible staff",
            'ExternalStaff': "External (non-TU/e) supervisor(s)",
            'Group': "Capacity group",
            'SecondaryGroup': "Secondary capacity group(s)",
            'NumStudentsMin': "Minimum number of students",
            'NumStudentsMax': "Maximum number of students",
            'GeneralDescription': "General description",
            'StudentsTaskDescription': "Students task description",
            'StartDate': "Visible from (empty for always)",
            'EndDate': "Visible till (empty for always)",
            'Apply': 'How can students apply',
            'Program': 'Specialization (leave blank for all)',
            'RecommendedCourses': 'Recommended courses (blank for none)',
            'SiteUrl': 'Site URL'
        }
        widgets = {
            'Title': widgets.MetroTextInput,
            'ResponsibleStaff': widgets.MetroSelect,
            'ExternalStaff': widgets.MetroMultiTextInput,
            'Assistants': widgets.MetroSelectMultiple,
            'GeneralDescription': widgets.MetroMarkdownInput,
            'StudentsTaskDescription': widgets.MetroMarkdownInput,
            'Group': widgets.MetroSelect,
            'SecondaryGroup': widgets.MetroSelectMultiple,
            'NumStudentsMin': widgets.MetroNumberInput,
            'NumStudentsMax': widgets.MetroNumberInput,
            'StartDate': widgets.MetroDateInput,
            'EndDate': widgets.MetroDateInput,
            'Program': widgets.MetroSelectMultiple,
            'Type': widgets.MetroSelect,
            'Apply': widgets.MetroSelect,
            'RecommendedCourses': widgets.MetroSelectMultiple,
            'SiteUrl': widgets.MetroTextInput,
            'Labels': widgets.MetroSelectMultipleColor,
        }

    def clean_addAssistantsEmail(self):
        """
        Clean email addresses and check their domain.
        convert email to user object, create if not exists.

        :return: assistant user accounts, as list
        """
        data = self.cleaned_data['addAssistantsEmail']
        accounts = []
        if data:
            for email in data.split('\n'):
                email = clean_email_default(email, settings.ALLOWED_PROJECT_ASSISTANT_DOMAINS)
                account = get_or_create_user_email(email, student=False)
                if account:
                    accounts.append(account)
                else:
                    raise ValidationError("User with email {} is invalid. Please contact support staff to resolve this issue.".format(email))
        return accounts

    def clean_Group(self):
        group = self.cleaned_data['Group']
        if self.request.user.groups.count() == 1 and get_grouptype('groupadministrator') in self.request.user.groups.all():
            # user is groupadmin and not assistant/responsible.
            rw_groups = get_writable_admingroups(self.request.user)
            if group not in rw_groups:
                raise ValidationError("You are not allowed to create a project for that group. You are only allowed to "
                                      "create projects for {}".format(print_list(rw_groups)))
        return group

    def clean(self):
        """
        Merge Private and addPrivatesEmail to Private, Merge addAssistantsEmail and Assistants to Assistants
        Verify validity of added users via email.
        Make sure the Private and Assistant dropdown field exist on the form,
        otherwise addAssistantEmail and addPrivateEmail are not saved.

        make sure Group is not in SecondaryGroup

        :return: updated Assistants and Privates
        """
        cleaned_data = super().clean()
        # add and check assistants.
        assistants = []
        if self.cleaned_data.get('Assistants'):
            assistants += self.cleaned_data.get('Assistants')
        if self.cleaned_data.get('addAssistantsEmail'):
            assistants += self.cleaned_data.get('addAssistantsEmail')
        assistants = set(assistants)
        for account in assistants:
            if account == self.cleaned_data.get('ResponsibleStaff'):
                raise ValidationError("The responsible staff member cannot be assistants of its own project.")
            # for assistants added using email, the queryset is not checked, so check groups now.
            if get_grouptype('assistants') not in account.groups.all() and \
                    get_grouptype('unverified') not in account.groups.all() and \
                    get_grouptype('supervisors') not in account.groups.all():
                raise ValidationError(
                    "The user {} is not allowed as assistant. Please contact the support staff if this user needs to be added.".format(account.usermeta.get_nice_name()))
        self.cleaned_data['Assistants'] = assistants

        if self.cleaned_data.get("Group") in self.cleaned_data.get("SecondaryGroup"):
            raise ValidationError("The primary capacity group of the project is not allowed as secondary group")

        return cleaned_data

    def save(self, commit=True):
        if commit:
            super().save(commit=True)
            # if no assistants, set to status 2
            if self.instance.Status == 1 and not self.instance.Assistants.exists():
                self.instance.Status = 2
        self.instance.save()
        return self.instance


class ProjectFormEdit(ProjectForm):
    """
    Edit an existing project.
    Mail changed assistants or changed responsible on edit.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # memorize responsible to be able to mail them if needed
        self.oldResponsibleStaff = self.instance.ResponsibleStaff

    class Meta(ProjectForm.Meta):
        pass

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data

    def save(self, commit=True):
        if commit:
            # add or remove assistants and external and notify them by mail.
            if 'Assistants' in self.changed_data:
                # assistant removed
                for ass in self.instance.Assistants.all():
                    if ass not in self.cleaned_data['Assistants']:
                        mail_project_single(self.instance, ass, "You were removed as assistant from:")
                # new assistant added
                for ass in self.cleaned_data['Assistants']:
                    if ass not in self.instance.Assistants.all():
                        mail_project_single(self.instance, ass, "You were added as assistant to:")
            # if 'ExternalStaff' in self.changed_data:
            #     # external removed via dropdown
            #     for ext in self.instance.ExternalStaff.all():
            #         if ext not in self.cleaned_data['ExternalStaff']:
            #             mail_project_single(self.instance, ext, "You were removed as external staff from:")
            #     # new assistant added via dropdown
            #     for ext in self.cleaned_data['ExternalStaff']:
            #         if ext not in self.instance.ExternalStaff.all():
            #             mail_project_single(self.instance, ext, "You were added as external staff to:")

            if 'ResponsibleStaff' in self.changed_data:
                if self.instance.ResponsibleStaff != self.oldResponsibleStaff:
                    mail_project_single(self.instance, self.oldResponsibleStaff,
                                        "You were removed as responsible staff from:")
                    mail_project_single(self.instance, self.instance.ResponsibleStaff,
                                        "You were added as responsible staff to:")
            # only save here, because old data is needed to determine changed privates.
            super().save(commit=True)
            self.instance.save()
        return self.instance


class ProjectFormCreate(ProjectForm):
    """
    Form to create a project.
    """
    # copy field to store a possible copied proposals original, to be able to copy images/attachments later on.
    copy = forms.ModelChoiceField(queryset=Project.objects.all(), required=False, widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        if 'copy' in kwargs.keys():
            pk = kwargs.pop('copy', None)
            super().__init__(*args, **kwargs)
            self.fields['copy'].initial = pk
        else:
            super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data

    def save(self, commit=True):
        if commit:
            super().save(commit=True)
            # if type2 created this project
            if get_grouptype("assistants") in self.request.user.groups.all():  # in master unverified cannot create project
                self.instance.Assistants.add(self.request.user)  # in case assistant forgets to add itself
            # elif get_grouptype("external") in self.request.user.groups.all():
            #     self.instance.ExternalStaff.add(self.request.user)  # in case assistant forgets to add itself
            # mailing users on this project is done in the view.
            self.instance.save()
            if self.cleaned_data['copy']:
                # do not copy assistants
                p = self.cleaned_data['copy']
                if p.images.exists():
                    for a in p.images.all():
                        f = ContentFile(a.File.read())
                        b = ProjectImage(
                            Caption=a.Caption,
                            OriginalName=a.OriginalName,
                            Project=self.instance,
                        )
                        b.File.save(ProjectFile.make_upload_path(b, a.OriginalName), f, save=False)
                        b.full_clean()  # This will crash hard if an invalid type is supplied, which can't happen
                        b.save()
                if p.attachments.exists():
                    for a in p.attachments.all():
                        f = ContentFile(a.File.read())
                        b = ProjectAttachment(
                            Caption=a.Caption,
                            OriginalName=a.OriginalName,
                            Project=self.instance,
                        )
                        b.File.save(ProjectFile.make_upload_path(b, a.OriginalName), f, save=False)
                        b.full_clean()  # This will crash hard if an invalid type is supplied, which can't happen
                        b.save()
        return self.instance


class ProjectImageForm(FileForm):
    class Meta(FileForm.Meta):
        model = ProjectImage

    def clean_File(self):
        return clean_image_default(self)


class ProjectAttachmentForm(FileForm):
    class Meta(FileForm.Meta):
        model = ProjectAttachment

    def clean_File(self):
        return clean_attachment_default(self)


class ProjectDowngradeMessageForm(forms.ModelForm):
    class Meta:
        model = ProjectStatusChange
        fields = ['Message']
        widgets = {
            'Message': widgets.MetroMultiTextInput,
        }
        labels = {"Message": "Message, leave blank for no message"}


class DistributionForm(forms.Form):
    """
    Form to distribute a student to a project
    """
    Students = forms.ModelMultipleChoiceField(widget=widgets.MetroSelectMultiple,
                                              required=False,
                                              queryset=User.objects.filter(groups__isnull=True, is_superuser=False),
                                              label='Choosen Students:')

    def __init__(self, *args, **kwargs):
        # Show user's full name as option item.
        super(DistributionForm, self).__init__(*args, **kwargs)
        self.fields['Students'].label_from_instance = lambda obj: "%s" % obj.usermeta.get_nice_name()


class ProgressForm(forms.ModelForm):
    """
    Form to set progress of project
    """

    class Meta:
        model = Project
        fields = ['Progress']
        help_texts = {
            'Progress': 'Set the progress status of the project. Leave blank for a not-yet started project.'
        }
        widgets = {
            'Progress': widgets.MetroSelect,
        }


class ProjectLabelForm(forms.ModelForm):
    """
    Form to change project labels
    """

    def clean_Color(self):
        color = self.cleaned_data['Color']
        if ProjectLabel.objects.filter(Color=color).exists():
            if self.instance.id:
                for obj in ProjectLabel.objects.filter(Color=color).all():
                    if obj.id != self.instance.id:
                        raise ValidationError("Another label uses this color. Please choose another color for this label")
            else:
                raise ValidationError("Another label uses this color. Please choose another color for this new label")
        return color

    class Meta:
        model = ProjectLabel
        fields = ['Name', 'Color']
        widgets = {
            'Name': widgets.MetroTextInput,
            'Color': widgets.MetroSelect,
        }

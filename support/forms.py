from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User, Group
from django.forms import ValidationError

from general_form import clean_file_default
from general_model import get_ext, print_list, clean_text
from general_view import get_grouptype
from index.models import UserMeta
from registration.models import Registration
from studyguide.models import CapacityGroup
from templates import widgets
from .models import Promotion


def clean_promotionlogo_default(self):
    file = clean_file_default(self)
    if get_ext(file.name) not in settings.ALLOWED_PROMOTION_LOGOS:
        raise ValidationError('This file type is not allowed. Allowed types: '
                              + print_list(settings.ALLOWED_PROMOTION_LOGOS))
    return file


class PromotionForm(forms.ModelForm):
    """
    A form to upload a file. It has a filefield and a caption field. More fields can be added.
    """

    class Meta:
        model = Promotion  # when inherited, this model is usually overwritten. Studentfile is only used as default.
        fields = ['Organization', 'Text', 'CapacityGroups', 'File', 'Url', 'Visible']
        widgets = {
            'Organization': widgets.MetroTextInput,
            'Text': widgets.MetroMultiTextInput,
            'CapacityGroups': widgets.MetroSelectMultiple,
            'File': widgets.MetroFileInput,
            'Url': widgets.MetroTextInput,
            'Visible': widgets.MetroCheckBox
        }
        help_texts = {
            'Text': 'Informative text. Maximum 500 characters, only the first sentences are shown in the sidebar.',
            'CapacityGroups': 'Select all capacity groups that this promotion is most interesting for. Leave blank if there is no preference.'
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    def clean_File(self):
        """
        File is not required, but if it is supplied, it needs cleaning.

        :return:
        """
        return clean_file_default(self, required=False)

    def clean_CapacityGroups(self):
        cg = self.cleaned_data.get("CapacityGroups")
        if 0 < len(cg) == CapacityGroup.objects.count():
            raise ValidationError("It is not allowed to select all capacity groups.")
        return cg


class ChooseMailingList(forms.Form):
    """
    List to choose what people to mail
    """

    def __init__(self, *args, **kwargs):
        staff_options = kwargs.pop('staff_options')
        student_options = kwargs.pop('student_options')
        super().__init__(*args, **kwargs)
        self.fields['Staff'].choices = staff_options
        self.fields['Students'].choices = student_options
        self.fields['Year'].choices = sorted(set(list(Registration.objects.filter(Cohort__isnull=False).values('Cohort').distinct().values_list('Cohort', 'Cohort')) +
                                                 list(UserMeta.objects.filter(Cohort__isnull=False).values('Cohort').distinct().values_list('Cohort', 'Cohort'))))

    Subject = forms.CharField(widget=widgets.MetroTextInput,
                              label='Subject:',
                              help_text="Subject for your message. The text '{}' is placed in front of this text".format(settings.NAME_PRETTY),
                              initial='message from support staff')
    Message = forms.CharField(widget=widgets.MetroMultiTextInput,
                              label='Message:',
                              help_text='The body message of the email.')
    Staff = forms.MultipleChoiceField(widget=widgets.MetroSelectMultiple,
                                      label='Staff to mail:',
                                      required=False,
                                      help_text='Only staff with active or future projects will be mailed',
                                      )
    Students = forms.MultipleChoiceField(widget=widgets.MetroSelectMultiple,
                                         label='Students to mail:',
                                         required=False,
                                         help_text='Only students of selected Cohort will be mailed.')
    Year = forms.ChoiceField(widget=widgets.MetroSelect,
                             label='Cohort:',
                             help_text='Only students of this Cohort will be mailed.')
    SaveTemplate = forms.BooleanField(widget=widgets.MetroCheckBox,
                                      required=False,
                                      label='Save form as template',
                                      help_text='Save this mailing list as template.')

    def clean_Subject(self):
        return clean_text(self.cleaned_data.get('Subject'))

    def clean_Message(self):
        return clean_text(self.cleaned_data.get('Message'))


# class ChooseMailingList(forms.Form):
#     """
#     List to choose what people to mail
#     """
#
#     def __init__(self, *args, **kwargs):
#         options = kwargs.pop('options')
#         super().__init__(*args, **kwargs)
#         for option in options:
#             self.fields['people_{}'.format(option[0])] = forms.BooleanField(widget=widgets.MetroCheckBox,
#                                                                             label=option[1],
#                                                                             required=False)
#
#     subject = forms.CharField(widget=widgets.MetroTextInput,
#                               label='Subject: (leave empty for default)',
#                               required=False)
#     message = forms.CharField(widget=widgets.MetroMultiTextInput,
#                               label='Message (check this twice):')
#     group = forms.ModelChoiceField(queryset=CapacityGroup.objects.all(), widget=widgets.MetroSelect,
#                                    label='Group: (only for students, leave empty for all)', required=False)
#     ccmyself = forms.BooleanField(widget=widgets.MetroCheckBox, label='Send copy to me:', required=False, initial=True)
#

class GroupadministratorEdit(forms.Form):
    """
    Form to assign groupadministrators to capacitygroups.
    """
    group = forms.ModelChoiceField(queryset=CapacityGroup.objects.all(), widget=widgets.MetroSelect,
                                   label='Capacity group:')
    readmembers = forms.ModelMultipleChoiceField(queryset=User.objects.filter(groups__isnull=False).distinct(),
                                                 widget=widgets.MetroSelectMultiple,
                                                 required=False, label='Administrators (read):')
    writemembers = forms.ModelMultipleChoiceField(queryset=User.objects.filter(groups__isnull=False).distinct(),
                                                  widget=widgets.MetroSelectMultiple,
                                                  required=False, label='Administrators (read/write):')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['readmembers'].label_from_instance = self.user_label_from_instance
        self.fields['writemembers'].label_from_instance = self.user_label_from_instance

    @staticmethod
    def user_label_from_instance(self):
        return self.usermeta.get_nice_name

    def clean(self):
        """
        Do not allow users to be in both read and write members.
        :return:
        """
        dups = set(self.cleaned_data.get('readmembers')) & set(self.cleaned_data.get('writemembers'))
        if dups:
            raise ValidationError(
                "User(s) {} cannot be both read and write members. Please remove them from one of the fields.".format(
                    print_list(list(dups))))


class UserGroupsForm(forms.ModelForm):
    """Form to assign groups to a user."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['groups'].queryset = Group.objects.exclude(name='unverified')

    class Meta:
        model = get_user_model()

        fields = ['groups']
        widgets = {'groups': widgets.MetroSelectMultiple}

    def clean_groups(self):
        groups = self.cleaned_data.get('groups')
        if len(groups) > 2:
            raise ValidationError("A user cannot be assigned more than two groups.")
        elif len(groups) == 2:
            # some invalid combinations:
            if get_grouptype('assistants') in groups and get_grouptype('supervisors') in groups:
                raise ValidationError(
                    "A user cannot be both assistant and supervisor. A project can have a supervisor member as assistant instead.")
            if get_grouptype('studyadvisors') in groups:
                if get_grouptype('directors') in groups:
                    raise ValidationError("studyadvisors has all rights director also has."
                                          " It is not possible to assign both.")
                # if get_grouptype('5') in groups:
                #     raise ValidationError("type3staff has all rights of type5staff also has. "
                #                           "It is not possible to assign both.")
        return groups

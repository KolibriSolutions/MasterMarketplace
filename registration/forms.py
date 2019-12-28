from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

from general_model import clean_text
from registration.models import RegistrationDeadline, RegistrationDeadlineDescription
from templates import widgets
from .models import Registration


class RegistrationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['Student'].disabled = True
        self.fields['Cohort'].disabled = True
        # self.fields['Electives'].queryset = Course.objects.filter(Year=get_year(), Type=1)  # Deprecated, replaced by courseplanner
        # self.fields['Electives'].label_from_instance = self.courses_label_from_instance

    @staticmethod
    def courses_label_from_instance(self):
        return "{} - {}".format(self.Code, self.Name)

    class Meta:
        model = Registration
        fields = ['Student', 'Cohort', 'Origin', 'Institute', 'Program']  # , 'Electives', 'OutOfFacultyCourses']
        widgets = {
            'Student': widgets.MetroSelect,
            'Cohort': widgets.MetroTextInput,
            'Origin': widgets.MetroSelect,
            'Institute': widgets.MetroTextInput,
            'Program': widgets.MetroSelect,
            # 'Electives' : widgets.MetroSelectMultiple,  # Deprecated, replaced by courseplanner
            # 'OutOfFacultyCourses' : widgets.MetroMultiTextInput,
        }
        labels = {
            'Program': 'Specialization Path',
            'OutOfFacultyCourses': 'Non ELE electives',
            'Institute': 'Institute (if not TU/e)',
        }
        help_texts = {
            'Student': 'This is the account you logged in with',
            'Cohort': 'The year you started with this study',
            'Origin': 'Where you came from',
            'Institute': 'If you selected "other institute" as origin, please give the name of the institute.',
            'Program': 'The specialization path you\'d like to take',
            # 'Electives': 'Elective courses. Do not fill in core courses (except when you chose them as elective). Do not choose courses already in your specialization path.',
            # 'OutOfFacultyCourses': 'Courses from other departments. Please mention the course code and name.',
        }


class AddOtherDepartmentCourseForm(forms.Form):
    """
    Form to add a course code
    """
    Code = forms.CharField(validators=[RegexValidator(settings.COURSECODEREGEX)], widget=widgets.MetroTextInput)

    def clean_Code(self):
        return clean_text(self.cleaned_data['Code'].upper())


class RegistrationDeadlineForm(forms.ModelForm):
    """
    Registration deadline form
    """
    class Meta:
        model = RegistrationDeadline
        fields = [
            'Type',
            'Stamp'
        ]
        widgets = {
            'Type': widgets.MetroSelect,
            'Stamp': widgets.MetroDateInput
        }

    # clean function to check type2 deadline is after type1 deadline.
    def clean(self):
        if self.cleaned_data.get('Type') == 2:
            deadline2 = self.cleaned_data.get("Stamp")
            try:
                deadline1 = RegistrationDeadline.objects.get(Type=1).Stamp
            except RegistrationDeadline.DoesNotExist:
                return
        elif self.cleaned_data.get('Type') == 1:
            deadline1 = self.cleaned_data.get("Stamp")
            try:
                deadline2 = RegistrationDeadline.objects.get(Type=2).Stamp
            except RegistrationDeadline.DoesNotExist:
                return
        else:
            raise Exception('Invalid deadline type (should never happen)')
        if deadline1 >= deadline2:
            raise ValidationError(
                "First deadline ({}) has to be before the second deadline ({})".format(deadline1, deadline2))


class RegistrationDeadlineDescriptionForm(forms.ModelForm):
    """
    Registration description form
    """

    class Meta:
        model = RegistrationDeadlineDescription
        fields = ['Title', 'Description']
        widgets = {
            'Title': widgets.MetroTextInput,
            'Description': widgets.MetroMultiTextInput
        }

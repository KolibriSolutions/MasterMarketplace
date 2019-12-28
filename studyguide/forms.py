from django import forms

from general_view import get_grouptype
from general_form import FileForm, clean_file_default
from general_model import get_ext, print_list
from registration.CourseBrowser import CourseBrowser
from templates import widgets
from . import models
from django.conf import settings


def clean_capgimage_default(self):
    file = clean_file_default(self)
    if get_ext(file.name) not in settings.ALLOWED_PUBLIC_FILES:
        raise forms.ValidationError('This file type is not allowed. Allowed types: '
                              + print_list(settings.ALLOWED_PUBLIC_FILES))
    return file


class MainCourseForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if kwargs['instance'] is None:  # a new course is allowed to edit code.
            self.fields['Code'].disabled = False
            self.new = True
        else:
            self.fields['Code'].disabled = True
            self.new = False

    class Meta:
        model = models.MainCourse
        fields = ['Code', 'Type', 'Year']
        widgets = {
            'Code': widgets.MetroTextInput,
            'Type': widgets.MetroSelect,
            'Year': widgets.MetroSelect,
        }

    def clean_Code(self):
        """
        Clean Code to be in uppercase.
        :return:
        """
        return self.cleaned_data['Code'].upper()

    def clean(self):
        """
        Get all other course data from courseBrowser.
        :return:
        """
        api = CourseBrowser(year=self.cleaned_data['Year'].Begin.year)
        try:
            header = api.get_course_data(self.cleaned_data['Code'])
        except:
            raise forms.ValidationError("An error occurred while communicating with CourseBrowser.")
        if header is None:
            raise forms.ValidationError("Course code is not known in CourseBrowser.")
        if self.new and models.MainCourse.objects.filter(Code=self.cleaned_data['Code'], Year=self.cleaned_data['Year']).exists():
            raise forms.ValidationError("A course with this code already exists for this year!")
        return self.cleaned_data


class MasterProgramForm(forms.ModelForm):
    class Meta:
        model = models.MasterProgram
        fields = ['Name', 'Group', 'MainCourses', 'DetailLink', 'Info', 'Year']
        widgets = {
            'Name': widgets.MetroTextInput,
            'MainCourses': widgets.MetroSelectMultiple,
            'Group': widgets.MetroSelectMultiple,
            'DetailLink': widgets.MetroTextInput,
            'Year': widgets.MetroSelect,
            'Info': widgets.MetroMarkdownInput,
        }

    def clean_MainCourses(self):
        main_courses = self.cleaned_data['MainCourses']
        if len(main_courses) != 2:
            raise forms.ValidationError("A specialization path should have two main courses.")
        return main_courses


class CapacityGroupForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['Head'].queryset = get_grouptype("supervisors").user_set.all()
        self.fields['Head'].label_from_instance = self.user_label_from_instance

    class Meta:
        model = models.CapacityGroup
        fields = ['ShortName', 'FullName', 'Info', 'Head']
        widgets = {
            'ShortName': widgets.MetroTextInput,
            'FullName': widgets.MetroTextInput,
            'Head': widgets.MetroSelect,
            'Info': widgets.MetroMarkdownInput,
        }

    @staticmethod
    def user_label_from_instance(self):
        return self.usermeta.get_nice_name


class CapacityGroupImageForm(FileForm):
    """Form to add a capacity group image"""

    class Meta(FileForm.Meta):
        model = models.CapacityGroupImage

    def clean_File(self):
        return clean_capgimage_default(self)


class MasterProgramImageForm(FileForm):
    """Form to add a master program image"""

    class Meta(FileForm.Meta):
        model = models.MasterProgramImage

    def clean_File(self):
        return clean_capgimage_default(self)


class MenuLinkForm(forms.ModelForm):
    """
    A form to add a link to the studyguide menu. Used for external links like digital studyguide
    """

    class Meta:
        model = models.MenuLink
        fields = ['Name', 'Url', 'Icon']
        widgets = {
            'Name': widgets.MetroTextInput,
            'Url': widgets.MetroTextInput,
            'Icon': widgets.MetroTextInput,
        }

# class CoursesImport(CsvUpload):
#     year = forms.ModelChoiceField(Year.objects.all(), widget=widgets.MetroSelect)

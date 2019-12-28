from django import forms
from django.conf import settings

from templates import widgets
from .models import AllowedAccess, Origin


class AccessForm(forms.ModelForm):
    class Meta:
        model = AllowedAccess
        fields = ['Email', 'Origin', 'Cohort']
        widgets = {
            'Email': widgets.MetroTextInput,
            'Origin': widgets.MetroSelect,
            'Cohort': widgets.MetroNumberInputInteger
        }

    def clean_Email(self):
        data = self.cleaned_data['Email'].lower()
        if data.split('@')[-1] not in settings.ALLOWED_ACCESSCONTROL_DOMAINS:
            raise forms.ValidationError("Only valid TU/e student emails are allowed")
        return data


class OriginForm(forms.ModelForm):
    class Meta:
        model = Origin
        fields = ['Name', 'Groups']
        widgets = {
            'Name': widgets.MetroTextInput,
            'Groups': widgets.MetroSelectMultiple,
        }

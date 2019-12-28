from django.forms import ValidationError

from general_form import clean_file_default, FileForm
from general_model import get_ext, print_list
from templates import widgets
from .models import FileExtension, StudentFile


def clean_studentfile_default(self):
    """
    Clean function for studentfile form. Checks if the extension is in the allowed extensions for this type file.

    :param self:
    :return:
    """
    file = clean_file_default(self)
    if get_ext(file.name) not in FileExtension.objects.all().values_list('Name', flat=True):
        raise ValidationError('This file extension is not allowed. Allowed extensions: '
                              + print_list(FileExtension.objects.all()))
    return file


class StudentFileForm(FileForm):
    """
    Upload or edit a studentfile
    """

    class Meta(FileForm.Meta):
        model = StudentFile
        fields = ['File', 'Caption']
        widgets = {
            'File': widgets.MetroFileInput,
            'Caption': widgets.MetroTextInput,
            # 'Type': widgets.MetroSelect
        }

    def clean_File(self):
        return clean_studentfile_default(self)

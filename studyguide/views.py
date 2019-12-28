import logging

from django.forms import modelformset_factory
from django.shortcuts import render, get_object_or_404

from general_form import ConfirmForm
from general_model import delete_object
from index.decorators import group_required, cache_for_students, cache_for_anonymous
from registration.CourseBrowser import CourseBrowser
from timeline.models import Year
from timeline.utils import get_year
from .forms import MasterProgramForm, CapacityGroupForm, MainCourseForm, CapacityGroupImageForm, MasterProgramImageForm
from .models import MasterProgram, CapacityGroup, MainCourse, CourseType, CapacityGroupImage, MasterProgramImage

logger = logging.getLogger('django')


@cache_for_students
@cache_for_anonymous
def list_years(request):
    """

    :param request:
    :return:
    """
    years = Year.objects.all()
    return render(request, 'studyguide/list_years.html', {
        'years': years,
    })


@cache_for_students
@cache_for_anonymous
def list_courses(request, year=None):
    """
    List courses

    :param request:
    :param year: pk of the year to filter on. Year to filter. 0 for all
    :return:
    """
    if year is None:  # get current year, no year supplied
        year = get_year()
    else:
        year = get_object_or_404(Year, pk=year)

    api = CourseBrowser(year=year.Begin.year)
    courses_per_type = {}
    for type in CourseType.objects.all():
        codes = [c.Code for c in type.courses.filter(Year=year)]
        courses = [item for sublist in api.get_list_courses_data(codes) for item in sublist]
        courses_per_type[str(type)] = courses

    return render(request, 'studyguide/list_courses.html', {
        'courses_per_type': courses_per_type,
        'year': year,
        'hide_sidebar': True
    })


@cache_for_students
@cache_for_anonymous
def list_master_programs(request, year=None):
    """
    List specialization paths

    :param request:
    :param year: Year to filter. 0 for all, None for current
    :return:
    """
    paths = MasterProgram.objects.all().prefetch_related('MainCourses', 'Group')
    if year is None:  # get current year, no year supplied
        year = get_year()
        paths = paths.filter(Year=year)
    elif year != 0:  # get specified year
        year = get_object_or_404(Year, pk=year)
        paths = paths.filter(Year=year)
    return render(request, 'studyguide/list_masterprograms.html', {
        'programs': paths,
        'year': year,
        'hide_sidebar': True,
    })


@cache_for_students
@cache_for_anonymous
def detail_master_program(request, pk):
    obj = get_object_or_404(MasterProgram, pk=pk)
    return render(request, 'studyguide/detail_masterprogram.html', {
        'program': obj
    })


@group_required('studyadvisors', 'directors')
def edit_master_program_images(request, pk):
    """
    Edit master_program images. Only for supportstaff
    These files are shown on the master program detail page.

    :param request:
    :param pk: pk of master program
    """
    mp = get_object_or_404(MasterProgram, pk=pk)
    form_set = modelformset_factory(MasterProgramImage, form=MasterProgramImageForm, can_delete=True, extra=0)
    qu = MasterProgramImage.objects.filter(MasterProgram=mp)
    formset = form_set(queryset=qu)

    if request.method == 'POST':
        formset = form_set(request.POST, request.FILES)
        if formset.is_valid():
            formset.save()
            return render(request, "base.html", {"Message": "File changes saved!", "return": "studyguide:detailmasterprogram", 'returnget': mp.pk})
    return render(request, 'GenericForm.html',
                  {'formset': formset, 'formtitle': 'All images of {}'.format(mp), 'buttontext': 'Save changes'})


@group_required('studyadvisors', 'directors')
def add_master_program_image(request, pk):
    """
    Add a image to master program

    :param request:
    :param pk: pk of the master program
    :return:
    """
    obj = get_object_or_404(MasterProgram, pk=pk)
    form = MasterProgramImageForm
    if request.method == 'POST':
        form = form(request.POST, request.FILES, request=request)
        if form.is_valid():
            file = form.save(commit=False)
            file.MasterProgram = obj
            file.save()
            return render(request, "base.html",
                          {"Message": "File saved!",
                           "return": 'studyguide:detailmasterprogram', 'returnget': obj.pk})

    return render(request, 'GenericForm.html',
                  {'form': form, 'formtitle': 'Add image to master program {}'.format(obj), 'buttontext': 'Save'})


@cache_for_students
@cache_for_anonymous
def list_capacity_groups(request):
    """
    List all capacity groups, edit buttons for support staff

    :param request:
    :return:
    """
    return render(request, 'studyguide/list_capacitygroups.html', {
        'groups': CapacityGroup.objects.all().select_related('Head'),
        'hide_sidebar': True
    })


@cache_for_students
@cache_for_anonymous
def detail_capacity_group(request, pk):
    group = get_object_or_404(CapacityGroup, pk=pk)
    return render(request, 'studyguide/detail_capacitygroup.html', {
        'group': group
    })


@cache_for_students
@cache_for_anonymous
def detail_capacity_group_name(request, shortname):
    group = get_object_or_404(CapacityGroup, ShortName=shortname)
    return render(request, 'studyguide/detail_capacitygroup.html', {
        'group': group
    })


@group_required('studyadvisors', 'directors')
def add_capacity_group(request):
    if request.method == 'POST':
        form = CapacityGroupForm(request.POST)
        if form.is_valid():
            obj = form.save()
            return render(request, 'base.html', {
                'Message': 'Capacity group {} added.'.format(obj.FullName),
                'return': 'studyguide:listcapacitygroups'
            })
    else:
        form = CapacityGroupForm()
    return render(request, 'GenericForm.html', {
        'form': form,
        'formtitle': 'Add New Capacity Group',
        'buttontext': 'Add',
        'upload_image': True,

    })


@group_required('studyadvisors', 'directors')
def edit_capacity_group(request, pk):
    obj = get_object_or_404(CapacityGroup, pk=pk)

    if request.method == "POST":
        form = CapacityGroupForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            return render(request, 'base.html', {
                'Message': 'Group {} saved.'.format(obj),
                'return': 'studyguide:listcapacitygroups',
            })
    else:
        form = CapacityGroupForm(instance=obj)

    return render(request, 'GenericForm.html', {
        'form': form,
        'formtitle': 'Edit Group',
        'buttontext': 'Save',
        'upload_image': True,
    })


@group_required('studyadvisors', 'directors')
def delete_capacity_group(request, pk):
    obj = get_object_or_404(CapacityGroup, pk=pk)
    if request.method == 'POST':
        form = ConfirmForm(request.POST)
        if form.is_valid():
            delete_object(obj)
            return render(request, 'base.html', {
                'Message': 'Capacity group {} deleted.'.format(obj),
                'return': 'studyguide:listcapacitygroups'
            })
    else:
        form = ConfirmForm()
    return render(request, 'GenericForm.html', {
        'form': form,
        'formtitle': 'Confirm deletion of {}'.format(obj),
        'buttontext': 'Delete'
    })


@group_required('studyadvisors', 'directors')
def edit_capacity_group_images(request, pk):
    """
    Edit cap group files. Only for supportstaff
    These files are shown on the capacitygroup detail page.

    :param request:
    """
    cg = get_object_or_404(CapacityGroup, pk=pk)
    form_set = modelformset_factory(CapacityGroupImage, form=CapacityGroupImageForm, can_delete=True, extra=0)
    qu = CapacityGroupImage.objects.filter(CapacityGroup=cg)
    formset = form_set(queryset=qu)

    if request.method == 'POST':
        formset = form_set(request.POST, request.FILES)
        if formset.is_valid():
            formset.save()
            return render(request, "base.html", {"Message": "File changes saved!", "return": "studyguide:detailcapacitygroup", 'returnget': cg.pk})
    return render(request, 'GenericForm.html',
                  {'formset': formset, 'formtitle': 'All images of {}'.format(cg.ShortName), 'buttontext': 'Save changes'})


@group_required('studyadvisors', 'directors')
def add_capacity_group_images(request, pk):
    """
    Add a image to capacity group

    :param request:
    :param pk: pk of the group
    :return:
    """
    obj = get_object_or_404(CapacityGroup, pk=pk)
    form = CapacityGroupImageForm
    if request.method == 'POST':
        form = form(request.POST, request.FILES, request=request)
        if form.is_valid():
            file = form.save(commit=False)
            file.CapacityGroup = obj
            file.save()
            return render(request, "base.html",
                          {"Message": "File saved!",
                           "return": 'studyguide:detailcapacitygroup', 'returnget': obj.pk})

    return render(request, 'GenericForm.html',
                  {'form': form, 'formtitle': 'Add image to capacity group {}'.format(obj.ShortName), 'buttontext': 'Save'})


@group_required('studyadvisors', 'directors')
def add_master_program(request):
    if request.method == 'POST':
        form = MasterProgramForm(request.POST)
        if form.is_valid():
            program = form.save()
            return render(request, 'base.html', {
                'Message': 'Program {} added.'.format(program),
                'return': 'studyguide:masterprogramlist'
            })
    else:
        form = MasterProgramForm()
    return render(request, 'GenericForm.html', {
        'form': form,
        'formtitle': 'Add New Specialization Path',
        'buttontext': 'Add',
        'upload_image': True,

    })


@group_required('studyadvisors', 'directors')
def edit_master_program(request, pk):
    obj = get_object_or_404(MasterProgram, pk=pk)

    if request.method == 'POST':
        form = MasterProgramForm(request.POST, instance=obj)
        if form.is_valid():
            program = form.save()
            return render(request, 'base.html', {
                'Message': 'Program {} edited.'.format(program),
                'return': 'studyguide:masterprogramlist'
            })
    else:
        form = MasterProgramForm(instance=obj)
    return render(request, 'GenericForm.html', {
        'form': form,
        'formtitle': 'Edit Specialization Path',
        'buttontext': 'Save',
        'upload_image': True,

    })


@group_required('studyadvisors', 'directors')
def delete_master_program(request, pk):
    obj = get_object_or_404(MasterProgram, pk=pk)

    if request.method == 'POST':
        form = ConfirmForm(request.POST)
        if form.is_valid():
            delete_object(obj)
            return render(request, 'base.html', {
                'Message': 'Program {} deleted.'.format(obj),
                'return': 'studyguide:masterprogramlist'
            })
    else:
        form = ConfirmForm()

    return render(request, 'GenericForm.html', {
        'form': form,
        'formtitle': 'Confirm deletion of {}'.format(obj),
        'buttontext': 'Delete'
    })


@group_required('studyadvisors', 'directors')
def main_course_form_view(request, code=None, year=None):
    if code is not None and year is not None:
        obj = get_object_or_404(MainCourse, Code=code, Year__Begin__year=year)
    else:
        obj = None

    if request.method == 'POST':
        form = MainCourseForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            return render(request, 'base.html', {
                'Message': 'Course saved.',
                'return': 'studyguide:courseslist'
            })
    else:
        form = MainCourseForm(instance=obj)

    return render(request, 'GenericForm.html', {
        'form': form,
        "formtitle": "Course Form",
        "buttontext": "Save",
    })


@group_required('studyadvisors', 'directors')
def delete_main_course(request, code, year):
    obj = get_object_or_404(MainCourse, Code=code, Year__Begin__year=year)
    if request.method == 'POST':
        form = ConfirmForm(request.POST)
        if form.is_valid():
            delete_object(obj)
            return render(request, 'base.html', {
                'Message': 'Main course {} deleted.'.format(obj),
                'return': 'studyguide:courseslist'
            })
    else:
        form = ConfirmForm()
    return render(request, 'GenericForm.html', {
        'form': form,
        'formtitle': 'Confirm deletion of {}'.format(obj),
        'buttontext': 'Delete'
    })

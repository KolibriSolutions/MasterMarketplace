import csv

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.shortcuts import render

from general_form import ConfirmForm, CsvUpload
from general_model import delete_object
from index.decorators import group_required
from .forms import AccessForm, OriginForm
from .models import AllowedAccess, Origin


@group_required('studyadvisors', 'directors')
def add_access(request):
    """
    Allow a student access to the system

    :param request:
    :return:
    """
    if request.method == "POST":
        form = AccessForm(request.POST)
        if form.is_valid():
            form.save()
            return render(request, 'base.html', {
                'Message': 'Access granted!',
                'return': 'accesscontrol:list'
            })
    else:
        form = AccessForm()

    return render(request, 'GenericForm.html', {
        'form': form,
        'formtitle': 'Grant New Access',
        'buttontext': 'Grant'
    })


@group_required('studyadvisors', 'directors')
def edit_access(request, pk):
    """
    Change student allowed access

    :param request:
    :param pk:
    :return:
    """
    try:
        obj = AllowedAccess.objects.get(pk=pk)
    except AllowedAccess.DoesNotExist:
        return render(request, 'base.html', {
            'Message': 'This user is not allowed access to the system.',
            'return': 'accesscontrol:list'
        })
    if request.method == "POST":
        form = AccessForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            return render(request, 'base.html', {
                'Message': 'Access Saved',
                'return': 'accesscontrol:list'
            })
    else:
        form = AccessForm(instance=obj)
    return render(request, 'GenericForm.html', {
        'form': form,
        'formtitle': 'Edit Access',
        'buttontext': 'Save'
    })


@group_required('studyadvisors', 'directors')
def delete_access(request, pk):
    """
    Remove allowed access of user. This disables student account.

    :param request:
    :param pk:
    :return:
    """
    obj = get_object_or_404(AllowedAccess, pk=pk)

    if request.method == "POST":
        form = ConfirmForm(request.POST)
        if form.is_valid():
            delete_object(obj)
            return render(request, 'base.html', {
                'Message': 'Access revoked',
                'return': 'accesscontrol:list'
            })
    else:
        form = ConfirmForm()

    return render(request, 'GenericForm.html', {
        'form': form,
        'formtitle': 'Revoke access to {}'.format(obj),
        'buttontext': 'Revoke'
    })


@group_required('studyadvisors', 'directors')
def list_access(request):
    """
    List all allowed access and possibly linked user.
    User is linked after first login using saml.

    :param request:
    :return:
    """
    allowed = AllowedAccess.objects.all().select_related().prefetch_related('User__registration')
    return render(request, 'accesscontrol/list_access.html', {
        'accesses': allowed
    })


@group_required('studyadvisors', 'directors')
def import_access(request):
    """
    import access from csv file
    example format:
    f.j.l.boerman@student.tue.nl,ES,2017

    :param request:
    :return:
    """
    if request.method == 'POST':
        error_list = ''
        form = CsvUpload(request.POST, request.FILES)
        if form.is_valid():
            numaccess = 0
            l = [x.decode().strip('\n') for x in request.FILES['csvfile'].read().splitlines()]
            for i, accesscsv in enumerate(
                    csv.reader(l, quotechar='"', delimiter=form.cleaned_data['delimiter'], quoting=csv.QUOTE_ALL,
                               skipinitialspace=True)):
                try:
                    if accesscsv[0].split('@')[-1].lower() not in settings.ALLOWED_ACCESSCONTROL_DOMAINS:
                        error_list += '<li>Email domain {} is not allowed. User {} is skipped.</li>'.format(accesscsv[0].split('@')[-1].lower(), accesscsv[0])
                        continue
                    new = True
                    try:
                        obj = AllowedAccess.objects.get(Email=accesscsv[0].lower())
                        new = False
                    except AllowedAccess.DoesNotExist:
                        obj = AllowedAccess()
                        obj.Email = accesscsv[0].lower()

                    if len(accesscsv) > 1:
                        try:
                            obj.Origin = Origin.objects.get(Name=accesscsv[1])
                        except Origin.DoesNotExist:
                            error_list += '<li>The origin {} is not known in the system. User {} is skipped.</li>'.format(accesscsv[1], accesscsv[0])
                            continue
                        if len(accesscsv) > 2:
                            obj.Cohort = int(accesscsv[2])
                    else:
                        if new:
                            obj.Origin = Origin.objects.get(Name='ELE')  # this origin should always exist.
                    try:
                        obj.save()
                    except:
                        error_list += '<li>Something went wrong while adding {}. This user is skipped.'.format(accesscsv)
                        continue
                    numaccess += 1
                except:
                    error_list += '<li>Something went wrong while adding {}. This user is skipped.'.format(accesscsv)
                    continue
            if error_list:
                return render(request, 'base.html', {
                    'Message': '{} valid access added or updated.<br /><p>The following error(s) occurred:</p><ul>{}</ul>'
                              .format(numaccess, error_list),
                    'return': 'accesscontrol:list',
                })
            else:
                return render(request, 'base.html', {
                    'Message': 'No errors occurred. <br />{} valid access added or updated'.format(numaccess),
                    'return': 'accesscontrol:list',
                })
    else:
        form = CsvUpload(initial={'delimiter': ','})

    return render(request, 'accesscontrol/csv_grant_form.html', {
        'form': form,
        'formtitle': 'Import Access From Csv',
        'button': 'Import'
    })


@group_required('studyadvisors', 'directors')
def create_origin(request):
    if request.method == 'POST':
        form = OriginForm(request.POST)
        if form.is_valid():
            form.save()
            return render(request, 'base.html', {
                'Message': 'Origin added!'
            })
    else:
        form = OriginForm()

    return render(request, 'GenericForm.html', {
        'form': form,
        'formtitle': 'Create new origin',
        'buttontext': 'Create'
    })


@group_required('studyadvisors', 'directors')
def edit_origin(request, pk):
    obj = get_object_or_404(Origin, pk=pk)
    if obj.Name == 'ELE':
        raise PermissionDenied("This origin cannot be edited.")

    if request.method == 'POST':
        form = OriginForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            return render(request, 'base.html', {
                'Message': 'Origin saved!',
                'return': 'accesscontrol:listorigins'
            })
    else:
        form = OriginForm(instance=obj)

    return render(request, 'GenericForm.html', {
        'form': form,
        'formtitle': 'Edit origin',
        'buttontext': 'Save'
    })


@group_required('studyadvisors', 'directors')
def list_origins(request):
    return render(request, 'accesscontrol/list_origins.html', {
        'origins': Origin.objects.all()
    })

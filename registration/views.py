from datetime import datetime

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.core.exceptions import PermissionDenied
from django.http.response import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from openpyxl.writer.excel import save_virtual_workbook

from general_form import ConfirmForm
from general_mail import send_mail
from general_view import get_grouptype
from index.decorators import group_required, student_only, ele_only
from registration.forms import RegistrationDeadlineForm, RegistrationDeadlineDescriptionForm
from registration.models import Registration, Planning, RegistrationDeadline, RegistrationDeadlineDescription
from studyguide.models import CapacityGroup, MasterProgram, CourseType, MainCourse
from tracking.models import RegistrationTracking
from .CourseBrowser import CourseBrowser
from .exports import get_approval_xlsx_filled
from .forms import RegistrationForm, AddOtherDepartmentCourseForm
from .models import PlannedCourse
from .utils import get_current_cohort, pack_header


@group_required('studyadvisors', 'directors')
def approve_registration(request, pk):
    obj = get_object_or_404(Registration, pk=pk)
    if request.method == "POST":
        form = ConfirmForm(request.POST)
        if form.is_valid():
            if obj.State != 3:
                obj.State = 3
                obj.save()
                send_mail('registration approved', 'email/registration_approved.html', {
                    'registration': obj,
                    'student': obj.Student,
                }, obj.Student.email)
                return render(request, 'base.html', {
                    'Message': 'Registration for {} approved and student notified.'.format(obj),
                    'return': 'registration:listall'
                })
            else:
                return render(request, 'base.html', {
                    'Message': 'Registration for {} was already approved.'.format(obj),
                    'return': 'registration:listall'
                })
    else:
        form = ConfirmForm()

    return render(request, 'registration/registration_confirm_form.html', {
        'registration': obj,
        'form': form,
        'formtitle': 'Are you sure to approve registration {}'.format(obj),
        'buttontext': 'Confirm',
    })


@group_required('studyadvisors', 'directors')
def disapprove_registration(request, pk):
    obj = get_object_or_404(Registration, pk=pk)
    if request.method == "POST":
        form = ConfirmForm(request.POST)
        if form.is_valid():
            if obj.State != 1:
                obj.State = 1
                obj.save()
                send_mail('registration disapproved', 'email/registration_disapproved.html', {
                    'registration': obj,
                    'student': obj.Student,
                }, obj.Student.email)
                return render(request, 'base.html', {
                    'Message': 'Registration for {} disapproved and student notified.'.format(obj),
                    'return': 'registration:listall'
                })
            else:
                return render(request, 'base.html', {
                    'Message': 'Registration for {} was not yet approved.'.format(obj),
                    'return': 'registration:listall'
                })
    else:
        form = ConfirmForm()

    return render(request, 'registration/registration_confirm_form.html', {
        'registration': obj,
        'form': form,
        'formtitle': 'Are you sure to disapprove registration {}'.format(obj),
        'buttontext': 'Confirm',
    })


@group_required('studyadvisors', 'directors')
def list_registrations(request, cohort=None):
    """
    List registrations of a cohort.

    :param request:
    :param cohort: cohort to list, none for current cohort.
    :return:
    """
    if not cohort:
        cohort = get_current_cohort()
    cohorts = sorted(list(Registration.objects.values('Cohort').distinct().values_list('Cohort', flat=True)))
    if cohort not in cohorts:
        cohorts.append(cohort)
    return render(request, 'registration/list_registrations.html', {
        'registrations': Registration.objects.filter(Cohort=cohort).select_related().prefetch_related('Student__usermeta'),
        'hide_sidebar': True,
        'cohort': cohort,
        'cohorts': cohorts,
    })


@student_only()
@ele_only()
def registration_view(request):
    try:
        obj = request.user.registration
        if request.user.usermeta.Cohort:
            # in case the Cohort is changed (in usermeta) after a registration is made, update the registration.
            if request.user.usermeta.Cohort != obj.Cohort:
                obj.Cohort = request.user.usermeta.Cohort
                obj.save()
        else:
            # in case usermeta.Cohort is empty, set it using the registration. This would usually not happen.
            request.user.usermeta.Cohort = obj.Cohort
            request.user.usermeta.save()
    except Registration.DoesNotExist:
        # new registration
        obj = Registration()
        obj.Student = request.user
        # cohort is set in usermeta on login based on allowedaccess.Cohort
        if not request.user.usermeta.Cohort:
            request.user.usermeta.Cohort = datetime.today().year
            request.user.usermeta.save()
        obj.Cohort = request.user.usermeta.Cohort

    if request.method == "POST":
        form = RegistrationForm(request.POST, instance=obj)
        if form.is_valid():
            if not form.has_changed():
                return render(request, 'base.html', {
                    'Message': 'Registration not changed.',
                    'return': 'registration:registrationform',
                })
            obj = form.save()

            # if _deadline_phase() != -1 and obj.Cohort == get_current_cohort():
            #     # Auto approve if student is from current cohort (new student) and at least one deadline exist.
            #     obj.Approved = True
            # else:
            #     obj.Approved = False
            #     # non threaded sending multiple because studyadvisors is never a lot of persons
            #     for advisor in Group.objects.get(name='studyadvisors').user_set.all():
            #         send_mail('student registration', 'email/changed_registration_studyadvisor.html', {
            #             'student': request.user,
            #             'diff': obj.diff(),
            #             'registration': obj,
            #         }, advisor.email)
            obj.save()
            # send_mail('registration', 'email/registration_confirmation.html', {
            #     'registration': obj,
            #     'student': request.user,
            # }, request.user.email)
            obj.State = 1

            track = RegistrationTracking()
            track.Student = request.user
            track.save()

            return render(request, 'base.html', {
                'Message': 'Registration is saved!',
                'return': 'registration:registrationform',
            })
    else:
        form = RegistrationForm(instance=obj)

    return render(request, 'registration/registration_form.html', {
        'form': form,
        'formtitle': 'Register For Specialization Path',
        'buttontext': 'Save',
        'approved': obj.get_State_display()
    })


@group_required('studyadvisors', 'directors', 'assistants', 'supervisors', 'groupadministrator')
def registration_stats(request, cohort=None):
    if cohort:
        r = Registration.objects.filter(Cohort=cohort)
    else:
        r = Registration.objects.all()

    totalnum = r.count()

    filters = Registration.objects.all().values_list('Cohort', flat=True).distinct()

    groups = CapacityGroup.objects.all()
    groupcount = []
    grouplabels = []
    for group in groups:
        groupcount.append(r.filter(Program__Group=group).count())
        grouplabels.append(str(group))
    if groupcount:
        groupcount, grouplabels = (list(t) for t in zip(*sorted(zip(groupcount, grouplabels), reverse=True)))

    groups = MasterProgram.objects.all()
    spec_count = []
    spec_labels = []
    for group in groups:
        spec_count.append(r.filter(Program=group).count())
        spec_labels.append(str(group))
    if spec_count:
        spec_count, spec_labels = (list(t) for t in zip(*sorted(zip(spec_count, spec_labels), reverse=True)))

    origin_count = []
    origin_labels = []
    for option in Registration.OriginChoices:
        origin_count.append(r.filter(Origin=option[0]).count())
        origin_labels.append(option[1])
    if origin_count:
        origin_count, origin_labels = (list(t) for t in zip(*sorted(zip(origin_count, origin_labels), reverse=True)))

    return render(request, 'registration/registration_stats.html', {
        'num': totalnum,
        'done': r.filter(State=3).count(),
        'filters': filters,
        'filter': cohort,
        'data': [
            {
                'label': 'Capacity groups',
                'labels': grouplabels,
                'counts': groupcount,
                'total': totalnum,
            }, {
                'label': 'Specialization paths',
                'labels': spec_labels,
                'counts': spec_count,
                'total': totalnum,
            }, {
                'label': 'Origin',
                'labels': origin_labels,
                'counts': origin_count,
                'total': totalnum,

            }
        ],
    })


@login_required()
def courseplanner(request, student_pk=None):
    api = CourseBrowser()
    if student_pk is None:
        # student view/edit
        user = request.user
        edit = True
        if user.groups.exists():
            raise PermissionDenied("This page is only for students.")
        if user.usermeta.Department != 'ELE':
            raise PermissionDenied("Only for ELE students")
    else:
        # staff member view only
        edit = False
        user = get_object_or_404(User, pk=student_pk)
        if get_grouptype('studyadvisors') not in request.user.groups.all() and \
                get_grouptype('directors') not in request.user.groups.all():
            raise PermissionDenied("Only for studyadvisors and directors!")

    try:
        reg = user.registration
    except Registration.DoesNotExist:
        raise PermissionDenied('Please fill in your registration first.')

    try:
        planning = reg.courseplanning
    except Planning.DoesNotExist:
        planning = Planning(Registration=reg)
        planning.save()

    # get the course headers for the specific types
    courses_per_type = []
    for type in CourseType.objects.all():  # core/specialization/profskill
        codes = list(set([c.Code for c in type.courses.all()]))  # dedup list of all courses known in the system from all years
        courses = [pack_header(h) for h in api.get_list_courses_data(codes)]  # get course info for current year.
        courses_per_type.append({
            'name': type.Name,
            'machinename': type.Name.lower().replace(' ', '_'),
            'courses': courses,
            'codes': codes,
        })

    # get courses for specialization
    program_courses_codes = [c.Code for c in reg.Program.MainCourses.all()]
    program_courses_data = [pack_header(h) for h in api.get_list_courses_data(program_courses_codes)]

    courses_per_type.append({
        'name': 'Specialization',
        'machinename' 'specialization'
        'codes': program_courses_codes,
        'courses': program_courses_data,
    })

    # if courses of out of faculty are added then add them to menu
    other_courses = planning.courses.exclude(Code__in=MainCourse.objects.values_list('Code', flat=True)).values_list('Code', flat=True)
    other_courses_data = []
    for c in other_courses:
        try:
            # tue course, use coursebrowser
            data = api.get_course_data(c)
            if data:
                header = pack_header(data)
            else:
                raise Exception("Non TU/e")
        except:
            # unknown course.
            header = {
                'code': c,
                'name': c,
                'timeslots': 'Unknown',
                'quartiles': [1, 2, 3, 4],
                'info': 'Outside TU/e',
                'link': '',
            }
        other_courses_data.append(header)

    courses_per_type.append({
        'name': 'Other courses',
        'machinename': 'outoffaculty',
        'codes': other_courses,
        'courses': other_courses_data
    })

    return render(request, 'registration/courseplanner.html', {
        'data': courses_per_type,
        'hide_sidebar': True,
        'yearrange': range(1, planning.Years + 1),
        'years': planning.Years,
        'registration': reg,
        'edit': edit,
    })


@student_only()
@ele_only()
def add_other_department_course(request):
    """
    Add course from other department and put it in the planning.

    :param request:
    :return:
    """
    if request.method == 'POST':
        form = AddOtherDepartmentCourseForm(request.POST)
        if form.is_valid():
            api = CourseBrowser()
            reg = request.user.registration

            try:
                planning = reg.courseplanning
            except Planning.DoesNotExist:
                planning = Planning(Registration=reg)
                planning.save()

            if MainCourse.objects.filter(Code=form.cleaned_data['Code']).exists():
                print('hoi')
                return render(request, 'base.html', {
                    'Message': 'This is an EE Graduate School course. Please select it using the drag-and-drop menu.',
                    'return': 'registration:courseplanner'
                })

            courseheader = api.get_course_data(form.cleaned_data['Code'])
            if courseheader is None:
                return render(request, 'base.html', {
                    'Message': 'This course code is not valid. Make sure the course code is correct and from TU/e at Osiris.tue.nl or coursebrowser.nl',
                    'return': 'registration:courseplanner'
                })
            courseheader = pack_header(courseheader)
            try:
                q = int(courseheader['quartiles'][0])
            except ValueError:
                q = 1
            c = PlannedCourse(Planning=planning, Year=1, Quartile=q, Code=courseheader['code'])
            c.save()

            return redirect('registration:courseplanner')

    else:
        form = AddOtherDepartmentCourseForm()

    return render(request, 'GenericForm.html', {
        "form": form,
        "formtitle": "Add course from other department",
        "buttontext": "Add",
    })


@student_only()
@ele_only()
def add_other_university_course(request):
    """
    Add course from other university and put it in the planning.

    :param request:
    :return:
    """
    if request.method == 'POST':
        form = AddOtherDepartmentCourseForm(request.POST)
        if form.is_valid():
            reg = request.user.registration
            try:
                planning = reg.courseplanning
            except Planning.DoesNotExist:
                planning = Planning(Registration=reg)
                planning.save()
            # prepend 'other_' to prevent name clashing with tu/e courses
            c = PlannedCourse(Planning=planning, Year=1, Quartile=1, Code=('other_' + form.cleaned_data['Code'])[:16])
            c.save()
            return redirect('registration:courseplanner')
    else:
        form = AddOtherDepartmentCourseForm()
    return render(request, 'GenericForm.html', {
        "form": form,
        "formtitle": "Add course from other university.",
        "buttontext": "Add",
    })


@student_only()
@ele_only()
def request_approval(request):
    try:
        reg = request.user.registration
    except Registration.DoesNotExist:
        raise PermissionDenied('Please fill in your registration and course planning first.')
    if reg.State == 1:
        reg.State = 2
        reg.save()
        for advisor in Group.objects.get(name='studyadvisors').user_set.all():
            send_mail('student registration', 'email/approval_requested.html', {
                'student': request.user
            }, advisor.email)
        send_mail('student registration', 'email/approval_requested.html', {  # also always email support
            'student': request.user
        }, settings.SUPPORT_EMAIL)
        return render(request, 'base.html', {
            'Message': 'Approval request send.'
        })
    elif reg.State == 3:
        return render(request, 'base.html', {
            'Message': 'Registration is already approved.'
        })
    else:
        return render(request, 'base.html', {
            'Message': 'Registration is already pending.'
        })


@student_only()
@ele_only()
def get_approvalform(request):
    try:
        wb = get_approval_xlsx_filled(request.user)
    except Exception as e:
        raise PermissionDenied("Downloading the approval excel file is not possible. Please contact support. (Error: {})".format(e))
    response = HttpResponse(content=save_virtual_workbook(wb))
    # else:
    #     response = HttpResponse("NOT TESTABLE")
    response['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response['Content-Disposition'] = 'attachment; filename=approvalform.xlsx'
    return response


@group_required('studyadvisors', 'directors')
def get_approvalform_support(request, pk):
    usr = get_object_or_404(User, pk=pk)
    try:
        wb = get_approval_xlsx_filled(usr)
    except Exception as e:
        raise PermissionDenied("Downloading the approval excel file is not possible. Please contact support. (Error: {})".format(e))

    response = HttpResponse(content=save_virtual_workbook(wb))
    # else:
    #     response = HttpResponse("NOT TESTABLE")
    response['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response['Content-Disposition'] = 'attachment; filename=approvalform-{}.xlsx'.format(usr.username)
    return response


@login_required
def deadlines(request):
    try:
        first = RegistrationDeadline.objects.get(Type=1).Stamp
    except RegistrationDeadline.DoesNotExist:
        first = "Not set"
    try:
        second = RegistrationDeadline.objects.get(Type=2).Stamp
    except RegistrationDeadline.DoesNotExist:
        second = "Not set"
    description = RegistrationDeadlineDescription.objects.first()
    if not description:
        description = RegistrationDeadlineDescription(Title='Description', Description="All deadlines are at 23:59 of the date listed on this page.")
        description.save()
    return render(request, 'registration/deadlines.html', {
        'first': first,
        'second': second,
        'description': description
    })


@group_required('studyadvisors', 'directors')
def deadline_form(request, t):
    """
    Set a deadline for registration

    :param request:
    :param t:
    :return:
    """
    t = int(t)
    if t > 2:
        raise PermissionDenied("This deadline does not exist.")
    if request.method == 'POST':
        form = RegistrationDeadlineForm(request.POST)
        if form.is_valid():
            try:
                obj = RegistrationDeadline.objects.get(Type=form.cleaned_data['Type'])
            except RegistrationDeadline.DoesNotExist:
                obj = RegistrationDeadline()
                obj.Type = form.cleaned_data['Type']
            obj.Stamp = form.cleaned_data['Stamp']
            obj.save()
            return render(request, 'base.html', {
                'Message': 'Deadline saved!',
                'return': 'registration:listall'
            })
    else:
        try:
            obj = RegistrationDeadline.objects.get(Type=t)
        except RegistrationDeadline.DoesNotExist:
            obj = None
        form = RegistrationDeadlineForm(instance=obj)
    return render(request, 'GenericForm.html', {
        'form': form,
        'formtitle': 'Set Registration Deadline',
        'buttontext': 'Set',
    })


@group_required('studyadvisors', 'directors')
def deadline_description_form(request):
    """
    Set a description text for registration

    :param request:
    :return:
    """
    obj = RegistrationDeadlineDescription.objects.first()
    if request.method == 'POST':
        form = RegistrationDeadlineDescriptionForm(request.POST, instance=obj)
        if form.is_valid():
            form.save(commit=True)
            return render(request, "base.html",
                          {"Message": "Description saved!", "return": "registration:deadlines"})
    else:
        form = RegistrationDeadlineDescriptionForm(instance=obj)
    return render(request, 'GenericForm.html',
                  {'form': form, 'formtitle': 'Edit deadline description text', 'buttontext': 'Save'})

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from projects.decorators import can_view_project
from students.decorators import can_apply
from index.decorators import student_only
from projects.models import Project
from tracking.models import ApplicationTracking
from .forms import StudentFileForm
from .models import Application, Distribution, StudentFile
from general_view import get_grouptype

@student_only()
def list_applications(request):
    """
    List the applications of a student, with a button to retract the application
    Also lists distributions.

    :param request:
    """
    projs = Project.objects.filter(Q(applications__Student=request.user) | Q(distributions__Student=request.user)).distinct()
    projlist = []
    for proj in projs:
        try:
            a = proj.applications.get(Student=request.user)
        except Application.DoesNotExist:
            a = None
        try:
            d = proj.distributions.get(Student=request.user)
        except Distribution.DoesNotExist:
            d = None
        x = {'project': proj, 'application': a, 'distribution': d}
        projlist.append(x)

    return render(request, "students/list_applications.html", context={
        'projlist': projlist
    })


@student_only()
def retract_application(request, application_id):
    """
    Let a user un-apply / retract an application.

    :param request:
    :param application_id: Application id
    """
    appl = get_object_or_404(Application, pk=application_id)
    if appl.Project.distributions.filter(Student=request.user).exists():
        raise PermissionDenied("You cannot retract this application, because you are distributed to this project. If this distribution is incorrect, please contact the responsible staff member of the project.")

    track = ApplicationTracking()
    track.Project = appl.Project
    track.Student = request.user
    track.Type = 'r'
    track.save()

    appl.delete()
    return render(request, "base.html", context={
        "Message": "Deleted application",
        "return": 'students:list_applications',
    })


@can_view_project
@can_apply
def apply(request, pk):
    """
    Let a user apply to a project. Called after confirmapply.

    :param request:
    :param pk: id of a project.
    """
    prop = get_object_or_404(Project, pk=pk)
    if request.user.applications.count() >= settings.MAX_NUM_APPLICATIONS:
        return render(request, "base.html", context={
            "Message": "already at max amount of applied projects<br>"
                       "retract one first before continuing",
            "return": 'students:list_applications',
        })
    if Application.objects.filter(Q(Project=prop) & Q(Student=request.user)).exists():
        return render(request, "base.html", context={
            "Message": "You already applied to this project.",
            "return": 'students:list_applications',
        })

    track = ApplicationTracking()
    track.Project = prop
    track.Student = request.user
    track.Type = 'a'
    track.save()

    appl = Application()
    appl.Project = prop
    # highestprio = request.user.applications.aggregate(Max('Priority'))['Priority__max']
    appl.Student = request.user
    # if highestprio is None:
    #     appl.Priority = 1
    # else:
    #     appl.Priority = highestprio + 1
    appl.save()
    return render(request, "base.html", context={
        "Message": "Application saved!",
        "return": 'students:list_applications',
    })


@can_view_project
@can_apply
def confirm_apply(request, pk):
    """
    After a student presses apply on a project, he/she has to confirm the application on this page.
    This page also checks whether the user is allowed to apply

    :param request:
    :param pk: id of the project
    """
    prop = get_object_or_404(Project, pk=pk)
    if Application.objects.filter(Q(Project=prop) & Q(Student=request.user)).exists():
        return render(request, "base.html", context={
            "Message": "You already applied to this project.",
            "return": 'students:list_applications',
        })
    return render(request, "students/apply.html", context={
        "project": get_object_or_404(Project, pk=pk),
    })


@login_required()
def list_files(request, dist):
    """
    List all files of a student on a distribution.

    :param request:
    :param dist: distribution to view files from.
    :return:
    """
    dist = get_object_or_404(Distribution, pk=dist)
    if request.user.groups.exists():
        if not (request.user in dist.Project.Assistants.all() or request.user == dist.Project.ResponsibleStaff or get_grouptype('studyadvisors') in request.user.groups.all()):
            # staff
            raise PermissionDenied("You are not allowed to view these student files.")
    elif request.user != dist.Student:
        # student
        raise PermissionDenied("You are not allowed to view this page.")

    files = dist.files.all()
    return render(request, 'students/list_files.html', context={
        'dist': dist,
        'files': files,
    })


@student_only()
def add_file(request, dist):
    """
    For students to upload a file. Used for the hand in system.
    Responsibles, assistants and trackheads can then view the files of their students.
    support staff can see all student files.

    :param request:
    :param dist: Distribution to add file to.
    """
    dist = get_object_or_404(Distribution, pk=dist)
    if request.user != dist.Student:
        raise PermissionDenied("You are not allowed to view this page.")

    if request.method == 'POST':
        form = StudentFileForm(request.POST, request.FILES, request=request)
        if form.is_valid():
            file = form.save(commit=False)
            file.Distribution = dist
            file.save()
            return render(request, 'base.html',
                          {'Message': 'File uploaded!', 'return': 'students:files', 'returnget': dist.pk})
    else:
        form = StudentFileForm(request=request)
    return render(request, 'GenericForm.html',
                  {'form': form, 'formtitle': 'Upload a file ', 'buttontext': 'Save'})


@student_only()
def edit_file(request, dist, file):
    """
    For students to edit a uploaded file. Used for the hand in system.
    Responsibles, assistants and trackheads can then view the files of their students.
    support staff can see all student files.

    :param request:
    :param dist: pk of Distribution of file
    :param file: pk of file
    """
    dist = get_object_or_404(Distribution, pk=dist)
    if request.user != dist.Student:
        raise PermissionDenied("You are not allowed to view this page.")
    file = get_object_or_404(StudentFile, pk=file, Distribution=dist)
    if request.method == 'POST':
        form = StudentFileForm(request.POST, request.FILES, request=request, instance=file)
        if form.is_valid():
            if form.has_changed():
                file = form.save(commit=False)
                file.Distribution = dist
                file.save()
                return render(request, 'base.html',
                              {'Message': 'File changed!', 'return': 'students:files', 'returnget': dist.pk})
            else:
                return render(request, 'base.html',
                              {'Message': 'No change made.', 'return': 'students:files', 'returnget': dist.pk})
    else:
        form = StudentFileForm(request=request, instance=file)
    return render(request, 'GenericForm.html',
                  {'form': form, 'formtitle': 'Edit file ', 'buttontext': 'Save'})

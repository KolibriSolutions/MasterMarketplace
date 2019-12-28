from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from general_view import get_grouptype
from projects.models import Project
from projects.utils import group_administrator_status, can_edit_project_fn, can_downgrade_project_fn, can_create_project_fn, can_delete_project_fn, can_distribute_project_fn, can_set_progress_project_fn


def can_view_project(fn):
    """
    Test if a given user is able to see a given project.

    :param fn:
    :return:
    """
    def wrapper(*args, **kw):
        if 'pk' in kw:
            pk = int(kw['pk'])
        else:
            pk = int(args[1])
        proj = get_object_or_404(Project, pk=pk)
        request = args[0]

        # user needs to be logged in (so no need for login_required on top of this)
        if not request.user.is_authenticated:
            page = args[0].path
            return redirect_to_login(
                next=page,
                login_url='index:login',
                redirect_field_name='next',)

        # support staf or superusers are always allowed to view
        if get_grouptype("studyadvisors") in request.user.groups.all() or request.user.is_superuser:
            return fn(*args, **kw)

        # user is staffmember and involved in the project
        if proj.ResponsibleStaff == request.user \
                or request.user in proj.Assistants.all():
            return fn(*args, **kw)

        # group administrators can view proposal
        if group_administrator_status(proj, request.user) > 0:
            return fn(*args, **kw)

        if get_grouptype('unverified') in request.user.groups.all():
            raise PermissionDenied("You are not allowed to view this project page, "
                                   "because your account is not yet verified.")

        # public projects.
        if proj.public_visible():
            if request.user.groups.exists():
                # staff can always see active proposals
                return fn(*args, **kw)
            # students
            else:
                ##No limitations on visibility based on master pogram.
                # if proj.Program.exists():
                #     # project only for some masterprograms
                #     if request.user.registration.Program in proj.Program.all():
                #         return fn(*args, **kw)
                #     else:
                #         raise PermissionDenied("This project is not visible for your Specialization Path.")
                # else: # project for all master programs.
                return fn(*args, **kw)

        # distributed student can view on project
        if proj.distributions.filter(Student=request.user).exists():
            return fn(*args, **kw)

        raise PermissionDenied("You are not allowed to view this project page.")

    return wrapper


def can_edit_project(fn):
    """
    Test if a user can edit a given project.

    :param fn:
    :return:
    """

    def wrapper(*args, **kw):
        if 'pk' in kw:
            pk = int(kw['pk'])
        else:
            pk = int(args[1])
        proj = get_object_or_404(Project, pk=pk)
        request = args[0]

        # user needs to be logged in (so no need for login_required on top of this)
        if not request.user.is_authenticated:
            page = args[0].path
            return redirect_to_login(
                next=page,
                login_url='index:login',
                redirect_field_name='next', )

        allowed = can_edit_project_fn(request.user, proj)
        if allowed[0] is True:
            return fn(*args, **kw)
        else:
            raise PermissionDenied(allowed[1])

    return wrapper


def can_downgrade_project(fn):
    """
    Test if a user can downgrade a given project.

    :param fn:
    :return:
    """

    def wrapper(*args, **kw):
        if 'pk' in kw:
            pk = int(kw['pk'])
        else:
            pk = int(args[1])
        proj = get_object_or_404(Project, pk=pk)
        request = args[0]

        # user needs to be logged in (so no need for login_required on top of this)
        if not request.user.is_authenticated:
            page = args[0].path
            return redirect_to_login(
                next=page,
                login_url='index:login',
                redirect_field_name='next', )

        allowed = can_downgrade_project_fn(request.user, proj)
        if allowed[0] is True:
            return fn(*args, **kw)
        else:
            raise PermissionDenied(allowed[1])

    return wrapper


def can_create_project(fn):
    """
    User is allowed to create project

    :param fn:
    :return:
    """
    def wrapper(*args, **kw):
        page = args[0].path
        request = args[0]
        # user needs to be logged in (so no need for login_required on top of this)
        if not request.user.is_authenticated:
            return redirect_to_login(
                next=page,
                login_url='index:login',
                redirect_field_name='next', )
        allowed = can_create_project_fn(request.user)
        if allowed[0] is True:
            return fn(*args, **kw)
        else:
            raise PermissionDenied(allowed[1])
    return wrapper


def can_delete_project(fn):
    def wrapper(*args, **kw):
        if 'pk' in kw:
            pk = int(kw['pk'])
        else:
            pk = int(args[1])
        page = args[0].path
        proj = get_object_or_404(Project, pk=pk)
        request = args[0]

        # user needs to be logged in (so no need for login_required on top of this)
        if not request.user.is_authenticated:
            return redirect_to_login(
                next=page,
                login_url='index:login',
                redirect_field_name='next', )

        allowed = can_delete_project_fn(request.user, proj)
        if allowed[0] is True:
            return fn(*args, **kw)
        else:
            raise PermissionDenied(allowed[1])
    return wrapper


def can_distribute_project(fn):
    """
    Test if a user can distribute students to a given project.

    :param fn:
    :return:
    """

    def wrapper(*args, **kw):
        if 'pk' in kw:
            pk = int(kw['pk'])
        else:
            pk = int(args[1])
        proj = get_object_or_404(Project, pk=pk)
        request = args[0]

        # user needs to be logged in (so no need for login_required on top of this)
        if not request.user.is_authenticated:
            page = args[0].path
            return redirect_to_login(
                next=page,
                login_url='index:login',
                redirect_field_name='next', )

        allowed = can_distribute_project_fn(request.user, proj)
        if allowed[0] is True:
            return fn(*args, **kw)
        else:
            raise PermissionDenied(allowed[1])
    return wrapper


def can_set_progress_project(fn):
    def wrapper(*args, **kw):
        if 'pk' in kw:
            pk = int(kw['pk'])
        else:
            pk = int(args[1])
        page = args[0].path
        proj = get_object_or_404(Project, pk=pk)
        request = args[0]

        # user needs to be logged in (so no need for login_required on top of this)
        if not request.user.is_authenticated:
            return redirect_to_login(
                next=page,
                login_url='index:login',
                redirect_field_name='next', )

        allowed = can_set_progress_project_fn(request.user, proj)
        if allowed[0] is True:
            return fn(*args, **kw)
        else:
            raise PermissionDenied(allowed[1])
    return wrapper

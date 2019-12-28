from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from projects.models import Project


def can_apply(fn):
    """
    Test if a student can apply or retract; The system is in timephase 3, user is a student and proposal is nonprivate.

    :param fn:
    :return:
    """

    def wrapper(*args, **kw):
        request = args[0]

        # user needs to be logged in (so no need for login_required on top of this)
        if not request.user.is_authenticated:
            page = args[0].path
            return redirect_to_login(
                next=page,
                login_url='index:login',
                redirect_field_name='next', )

        if request.user.groups.exists():
            raise PermissionDenied("Only students can apply to proposals")
        if 'pk' in kw:
            pk = int(kw['pk'])
            prop = get_object_or_404(Project, pk=pk)
            if not prop.public_visible():
                raise PermissionDenied("Error, project is not visible for students.")
            if prop.Progress == 2:
                raise PermissionDenied("Cannot apply, project is already finished")
            if prop.Progress == 3:
                raise PermissionDenied("Cannot apply, project is reserved")
            if prop.Apply == 'supervisor':
                raise PermissionDenied("To apply to this project, please contact the supervisor.")
        return fn(*args, **kw)

    return wrapper

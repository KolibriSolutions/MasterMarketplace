from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied

from general_view import get_grouptype
from registration.utils import check_api_key


def api_protected(fn):
    def wrapper(*args, **kw):
        request = args[0]
        if get_grouptype('studyadvisors') in request.user.groups.all():
            user = User.objects.get(pk=request.POST.get('view_user'))
            return fn(*args, **kw, user=user)
        key = request.POST.get('apikey', None)
        if key is None:
            raise PermissionDenied("api key error")
        if request.user.is_authenticated:
            user = request.user
        else:
            username = request.POST.get("username", None)
            if username is None:
                raise PermissionDenied("api key error")
            try:
                user = User.objects.get(username=username)
            except:
                raise PermissionDenied("api key error")

        if not check_api_key(user, key):
            raise PermissionDenied("api key error")
        return fn(*args, **kw, user=user)

    return wrapper

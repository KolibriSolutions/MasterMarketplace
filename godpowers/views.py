from importlib import import_module

from django.conf import settings
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.core.cache import cache
from django.http import HttpRequest
from django.shortcuts import render, get_object_or_404
from django.utils import timezone

from index.decorators import superuser_required
from general_view import get_sessions
from tracking.models import UserLogin


@superuser_required()
def clear_cache(request):
    """
    Clear the full REDIS cache

    :param request:
    :return:
    """
    cache.clear()
    return render(request, "base.html", {"Message": "Cache cleared!"})


@superuser_required()
def list_sessions(request):
    """
    List all active sessions (logged in users) with the possibility to kill a session (logout the user)

    :param request:
    """
    sessions = Session.objects.filter(expire_date__gte=timezone.now())
    uid_list = []

    for session in sessions:
        data = session.get_decoded()
        uid_list.append(data.get('_auth_user_id', None))
    users = []

    for user in User.objects.filter(id__in=uid_list):
        try:
            lastlogin = UserLogin.objects.filter(Subject=user).latest('Timestamp')
            users.append({'user': user, 'lastlogin': lastlogin})
        except:  # a session without a user (should not happen, only when user is deleted recently)
            pass

    return render(request, "godpowers/list_sessions.html", {"users": users})


def init_session(session_key):
    """
    Helper function to kill a session

    :param session_key:
    :return:
    """
    engine = import_module(settings.SESSION_ENGINE)
    return engine.SessionStore(session_key)


@superuser_required()
def kill_session(request, pk):
    """
    Kill a session of a user. Usually called from the list_sessions page.

    :param request:
    :param pk: id of the user to kill session for
    """
    user = get_object_or_404(User, pk=pk)
    sessions = get_sessions(user)
    if len(sessions) == 0:
        return render(request, "base.html", {"Message": "Could not find session.", "return": "godpowers:sessionlist"})
    for session in sessions:
        request = HttpRequest()
        request.session = init_session(session.session_key)
        auth_logout(request)
    return render(request, "base.html", {"Message": "User logged out.", "return": "godpowers:sessionlist"})

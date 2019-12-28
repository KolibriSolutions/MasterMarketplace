"""
General functions that are mostly used in views (views.py).
"""

from datetime import date

from django.conf import settings
from django.contrib.auth.models import Group, User
from django.contrib.sessions.models import Session
from django.core.cache import cache
from django.utils import timezone

from projects.models import Project


def get_grouptype(name):
    """
    Return the Group object

    :return:
    """
    gt = cache.get("gt" + name)
    if gt:
        return gt
    else:
        gt = Group.objects.get(name=name)
        cache.set("gt" + name, gt, settings.STATIC_OBJECT_CACHE_DURATION)
        return gt


def get_all_students():
    """
    Return all students of this cohort.

    :return: user objects
    """
    currentcohort = date.today().year
    if 1 <= date.today().month <= 8:
        # if the date is between january and august than the cohort started last year september.
        currentcohort -= 1
    return User.objects.filter(groups__isnull=True, registration__Cohort=currentcohort).distinct()


def get_all_staff():
    """
    Get all currently active staff.

    :return:
    """
    return User.objects.filter(groups__isnull=False).distinct()


def get_sessions(user):
    sessions = []
    for session in Session.objects.filter(expire_date__gte=timezone.now()):
        data = session.get_decoded()
        if data.get('_auth_user_id', None) == str(user.id):
            sessions.append(session)

    return sessions


def get_all_projects():
    return Project.objects.all()


def timestamp():
    """
    Timestamp for a xls export

    :return:
    """
    return "{:%Y-%m-%d %H:%M:%S}".format(timezone.now())


def truncate_string(data, trun_len=10):
    """
    Maybe replace with from django.template.defaultfilters import truncatechars

    :param data:
    :param trun_len:
    :return:
    """
    return (data[:trun_len] + '..') if len(data) > trun_len else data


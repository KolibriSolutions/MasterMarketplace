import json
from datetime import date
from io import BytesIO

import requests
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.core.signing import TimestampSigner
from openpyxl import load_workbook
from openpyxl.styles import Font

from registration.models import RegistrationDeadline, Planning, Registration
from studyguide.models import CourseType, MainCourse
from .CourseBrowser import CourseBrowser


def _deadline_phase():
    """
    Check whether registration deadlines are set or expired.
    Used to determine if registration is auto-approved or not.

    :return: -1 if deadline expired or not set. 1 if before deadline 1. 2 if before deadline 2.
    """
    try:
        deadline = RegistrationDeadline.objects.get(Type=1)
        if date.today() <= deadline.Stamp:
            # before or at deadline date
            return 1
    except RegistrationDeadline.DoesNotExist:
        pass
    try:
        deadline = RegistrationDeadline.objects.get(Type=2)
        if date.today() <= deadline.Stamp:
            # before or at deadline date
            return 2
    except:
        pass

    return -1


def get_current_cohort():
    """
    Get the current cohort. Year of start of academic year.

    :return: year as int
    """
    d = date.today()
    current_cohort = d.year
    if d.month < 9:
        current_cohort -= 1
    return current_cohort


def create_api_key(user):
    signer = TimestampSigner()
    return ':'.join(signer.sign(user.username).split(':')[1:])


def check_api_key(user, key):
    signer = TimestampSigner()
    try:
        signer.unsign("{}:{}".format(user.username, key), max_age=24 * 60 * 60)
        return True
    except:
        return False


def pack_header(header):
    """
    Gather information of course and bundle multiple instances with one code to one item.
    If a course is given in multiple quartiles header contains two courses. Return one.
    :param header:
    :return:
    """
    timeslots = [c['timeslot'] for c in header]
    quartiles = [str(c['quartile']) for c in header]
    # multiple timeslots are ignored for now.
    lst = ['Q{}-{}'.format(str(q), t) for q, t in zip(quartiles, timeslots)]
    info = "Given in: " + ';'.join(lst)
    course = header[0]

    return {
        'code': course['code'],
        'name': '{} - {}'.format(course['code'], course['name']),
        'timeslots': timeslots,
        'quartiles': quartiles,
        'info': info,
        'link': course['detaillink']
    }


def get_planning_json(courseplanning):
    planning = {}
    for y in range(1, courseplanning.Years + 1):
        for q in range(1, 5):
            planning["Y{}Q{}".format(y, q)] = []
    for c in courseplanning.courses.all():
        planning["Y{}Q{}".format(c.Year, c.Quartile)].append(c.Code)

    return planning

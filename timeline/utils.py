from datetime import datetime, date

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import AppRegistryNotReady
from django.db.models import Q

from timeline.models import Year


def get_year():
    """
    Return the current year object. Cached for 15 minutes.

    :return: object of the first timeslot at this time.
    """
    try:
        ts = cache.get('year')
        if ts:
            return ts
    except AppRegistryNotReady:
        pass

    now = datetime.now()
    try:
        ts = Year.objects.get(Q(Begin__lte=now) & Q(End__gte=now))
    except Year.DoesNotExist:
        y = now.year
        if now.month < 8:
            # second half year
            name = '{}-{}'.format(y - 1, y)
            start = date(year=y - 1, month=8, day=1)
            end = date(year=y, month=7, day=31)
        else:
            name = '{}-{}'.format(y, y + 1)
            start = date(y, month=8, day=1)
            end = date(year=y + 1, month=7, day=31)
        ts = Year(
            Name=name,
            Begin=start,
            End=end
        )
        ts.save()
    cache.set('year', ts, settings.STATIC_OBJECT_CACHE_DURATION)
    return ts


def get_year_id():
    """
    Returns the id of the current year, used for model initialization

    :return:
    """
    return get_year().pk

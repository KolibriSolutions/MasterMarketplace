from django.db.models import Q

from general_view import get_grouptype
from students.models import Distribution


def get_distributions(user):
    """
    Function to return the distributions that a given staff user is allowed to see
    Type3 and 6 should see all distributions, to be able to mail them.

    :param user: The user to test
    """
    des_all = Distribution.objects.all()
    if get_grouptype("directors") in user.groups.all() or \
            user.is_superuser or \
            get_grouptype("studyadvisors") in user.groups.all():
        return des_all
    else:
        return des_all.filter(Q(Project__ResponsibleStaff=user) |
                              Q(Project__Assistants__id=user.id) |
                              Q(Project__Group__Administrators=user.id)).distinct()

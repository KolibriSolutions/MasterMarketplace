from django import template

from general_view import get_grouptype

register = template.Library()


@register.simple_tag
def get_unverified_users():
    """
    return unverified users for type3staff/studyadvisor.

    :return:
    """
    val = get_grouptype('unverified').user_set.filter(is_active=True)
    val = val.values_list('usermeta__Fullname', flat=True)
    return val

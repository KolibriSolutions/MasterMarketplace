from datetime import date, datetime
from random import shuffle

from django import template
from django.conf import settings
from django.core.cache import cache
from django.db.models import Q
from django.utils.html import format_html

from general_view import get_grouptype
from index.models import Broadcast
from index.utils import markdown_safe, markdown_link_checker
from projects.utils import get_writable_admingroups
from studyguide.models import MenuLink
from support.models import Promotion

register = template.Library()


@register.filter(name='has_group')
def has_group(user, group_names):
    """
    Check groups for given user.

    :param user:
    :param group_names:
    :return:
    """
    if user.is_anonymous:
        return False
    if user.is_superuser:
        if group_names == "students":
            return False
        else:
            return True
    if group_names == "any":
        if user.groups.exists():
            return True
        else:
            return False
    elif group_names == "students":
        if not user.groups.exists():
            return True
        else:
            return False
    # check groups
    for group_name in group_names.split(';'):
        group = get_grouptype(group_name)
        if group in user.groups.all():
            return True
    return False


@register.filter(name='is_writable_groupadmin')
def is_writable_groupadmin(user):
    return len(get_writable_admingroups(user)) != 0


@register.simple_tag
def get_broadcasts(user):
    """

    :param user:
    :return:
    """
    msgs = Broadcast.objects.filter((Q(DateBegin__lte=datetime.now()) | Q(DateBegin__isnull=True)) &
                                    (Q(DateEnd__gte=datetime.now()) | Q(DateEnd__isnull=True)) &
                                    (Q(Private=user) | Q(Private__isnull=True))
                                    )
    if not msgs.exists():
        return "No announcements"

    if msgs.count() > 1:
        msg = "<ul>"
        for m in msgs:
            msg += "<li>{}</li>".format(m.Message)
        msg += "</ul>"
    else:
        msg = msgs[0]

    return format_html(str(msg))


@register.simple_tag
def broadcast_available(user):
    """

    :param user:
    :return:
    """
    if not user.is_authenticated:
        return False
    if Broadcast.objects.filter((Q(DateBegin__lte=datetime.now()) | Q(DateBegin__isnull=True)) &
                                (Q(DateEnd__gte=datetime.now()) | Q(DateEnd__isnull=True)) &
                                (Q(Private=user) | Q(Private__isnull=True))
                                ).exists():
        return True
    else:
        return False


@register.filter
def is_ele(user):
    return user.usermeta.Department == 'ELE'


@register.filter
def is_current_cohort(user):
    meta = user.usermeta
    if not meta.Cohort:
        return False
    d = date.today()
    current_cohort = d.year
    if d.month < 9:
        current_cohort -= 1
    return user.usermeta.Cohort == current_cohort


@register.simple_tag
def get_promotions(user):
    # promotions ordered by increasing number of CapacityGroups
    promotions = list(Promotion.objects.filter(Visible=True).prefetch_related('CapacityGroups'))
    if not user.groups.exists():
        #  student
        try:
            reg = user.registration.Program.Group.all()
            l1 = []  # list of interesting promotions for student
            l2 = []  # list with other promotions
            for promotion in promotions:
                if promotion.CapacityGroups.all():
                    if any([(cg in reg) for cg in promotion.CapacityGroups.all()]):
                        # promotion is interesting for user
                        l1.append(promotion)
                    else:
                        l2.append(promotion)
                else:
                    # promotion has no preferred capacity group
                    l2.append(promotion)
            shuffle(l1)
            shuffle(l2)  # randomize the other promotions
            return l1 + l2
        except:
            # user has no registration
            pass
    shuffle(promotions)
    return promotions  # shuffle is probably faster than .order_by('?')


@register.simple_tag
def get_menu_links():
    ml = cache.get('menulinks')
    if not ml:
        ml = MenuLink.objects.all()
        cache.set('menulinks', ml, settings.STATIC_OBJECT_CACHE_DURATION)
    return ml


@register.filter
def show_markdown(text):
    return format_html(markdown_safe(text))


@register.filter
def show_markdown_restricted(text):
    return format_html(markdown_safe(markdown_link_checker(text)))


@register.simple_tag
def get_max_upload_size():
    return settings.MAX_UPLOAD_SIZE

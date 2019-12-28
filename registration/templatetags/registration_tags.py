from django.utils.html import format_html

from registration.models import Registration
from registration.utils import create_api_key
from templates.templatetags.custom_filters import register


@register.filter
def create_registration_key(user):
    return create_api_key(user)


@register.simple_tag
def registration_status():
    num_non_approved = Registration.objects.filter(State=2).count()
    num_registrations = Registration.objects.count()

    if num_non_approved == 0:
        return format_html("All filed registrations have been approved of {} total.", num_registrations)
    else:
        return format_html("<span class='fg-red'> {} registrations waiting for approval</span> <br/> of {} total.",
                           num_non_approved, num_registrations)

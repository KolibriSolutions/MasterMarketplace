from django.conf import settings


def general(request=None):
    return {
        'DOMAIN': settings.DOMAIN,
        'CONTACT_EMAIL': settings.CONTACT_EMAIL,
        'NAME': settings.NAME_PRETTY,
    }


def debugsetting(request=None):
    """

    :param request:
    :return:
    """
    return {
        'DEBUG': settings.DEBUG
    }

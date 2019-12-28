from oauthlib.oauth2 import WebApplicationClient, MissingCodeError
from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponseNotFound
import requests
from django.core import serializers
from django.contrib.auth.models import User
from django.db.models import Q
from django.contrib import auth
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from general_view import get_grouptype
from django.middleware import csrf
from django.core import signing
import json
from accesscontrol.models import AllowedAccess
from django.contrib.auth.models import Group
from accesscontrol.models import AccessGrantStaff
from django.views.decorators.csrf import ensure_csrf_cookie
import base64
from django.utils.http import is_safe_url
from MasterMarketplace.utils import get_user


def set_level(user):
    try:
        grant = AccessGrantStaff.objects.get(Email=user.email)
    except AccessGrantStaff.DoesNotExist:
        return

    if grant.Level == 1:
        user.groups.add(get_grouptype("supervisors"))
        user.save()
    if grant.Level == 2:
        if get_grouptype("unverified") in user.groups.all():
            user.groups.remove(get_grouptype("unverified"))
        user.groups.add(get_grouptype("assistants"))
        user.save()


def set_osiris(user, osirisdata):
    """
    Set usermeta based on osiris data

    :param user:
    :param osirisdata:
    :return:
    """
    meta = user.usermeta
    if not meta.Overruled:
        if osirisdata.automotive:
            meta.Study = 'Automotive'
        else:
            meta.Study = 'Eletrical Engineering'
        meta.Cohort = osirisdata.cohort
        meta.ECTS = osirisdata.ects
        meta.Studentnumber = osirisdata.idnumber
        meta.full_clean()
        meta.save()


def is_staff(user):
    """
    Check whether the user is staff. Staff has an @tue.nl email, students have @student.tue.nl email.

    :param user:
    :return:
    """
    if user.email.split('@')[-1].lower() in settings.STAFF_EMAIL_DOMAINS:
        return True
    return False


def enrolled_osiris(user):
    """
    Check whether the user is enrolled in Osiris for the Master program

    :param user:
    :return:
    """
    return True


def check_user(request, user):
    meta = user.usermeta  # meta is generated if not exist in signal handler pre_user_save.
    # insert checks on login here
    if user.is_superuser:
        return render(request, 'base.html', status=403, context={
            'Message': 'Superusers are not allowed to login via SSO. Please use 2FA login.'})
    else:
        if is_staff(user):
            # staff, should have valid group
            unverified_grp = Group.objects.get(name="unverified")
            set_level(user)
            if not user.groups.exists():
                user.groups.add(unverified_grp)
                user.save()
            if unverified_grp in user.groups.all():
                return render(request, 'base.html', status=403, context={
                    'Message': 'You do not have the required permission to login yet. Please contact the {} {}'.
                              format(settings.SUPPORT_ROLE, settings.SUPPORT_NAME)}
                              )
        else:
            # student, should not have groups
            if user.groups.exists():
                user.groups.clear()
                user.save()
            try:  # replace by enrolled_osiris after osiris link is complete.
                access_obj = AllowedAccess.objects.get(Email=user.email.lower())
            except AllowedAccess.DoesNotExist:
                return render(request, 'base.html', status=403, context={
                    'Message': 'You do not have the required permission to login. Please contact the {} {}'.
                              format(settings.SUPPORT_ROLE, settings.SUPPORT_NAME)}
                              )
            # save relation
            access_obj.User = user
            access_obj.save()
            meta.Cohort = access_obj.Cohort
            meta.Department = access_obj.Origin.Name
            meta.full_clean()
            meta.save()
    return True


def callback(request):
    # parse the incoming answer from oauth
    client = WebApplicationClient(settings.SHEN_RING_CLIENT_ID)
    try:
        response = client.parse_request_uri_response(request.build_absolute_uri())
    except MissingCodeError:
        if 'error' in request.GET:
            raise PermissionDenied(request.GET.get('error'))
        else:
            raise PermissionDenied("Authentication failed")

    if not settings.SHEN_RING_NO_CSRF:
        if 'state' not in response:
            raise PermissionDenied("Authentication failed. (csrf state not available)")

        if '-' in response['state']:
            csrf_token, next_url = response['state'].split('-')
            next_url = base64.b64decode(next_url.encode()).decode()
        else:
            csrf_token = response['state']
            next_url = None

        if request.session.get(csrf.CSRF_SESSION_KEY, '') != csrf_token:
            raise PermissionDenied("Authentication failed. (csrf token failed)")
    else:
        if '-' in response.get('state', ""):
            next_url = base64.b64decode(response['state'].strip('-').encode()).decode()
        else:
            next_url = None

    # upgrade grant code to access code
    session = requests.Session()
    session.headers['User-Agent'] = settings.NAME_PRETTY
    # get parameters
    data = client.prepare_request_body(code=response['code'], client_secret=settings.SHEN_RING_CLIENT_SECRET,
                                       include_client_id=True)
    # convert to requests dictionary
    data_dict = {}
    for itm in data.split("&"):
        data_dict[itm.split('=')[0]] = itm.split('=')[1]

    # request accesstoken
    try:
        access_code_data = requests.post(settings.SHEN_RING_URL + "oauth/token/", data=data_dict).json()
    except:
        raise PermissionDenied("Authentication failed. (invalid_json_data)")
    if 'access_token' not in access_code_data:
        raise PermissionDenied(access_code_data['error'])

    # request account information
    # this assumes that timeslot pk is identical on both shen and local db!
    r = session.get(settings.SHEN_RING_URL + "info/", headers={"Authorization": "Bearer {}".format(access_code_data["access_token"])})

    if r.status_code != 200:
        raise PermissionDenied("Authentication failed. (shen_link_failed)")

    try:
        value = json.dumps(signing.loads(r.text, settings.SHEN_RING_CLIENT_SECRET))
    except signing.BadSignature:
        raise PermissionDenied("Authentication failed. (shen_signing_failed)")

    # login or create the user
    try:
        user, usermeta = serializers.deserialize('json', value)
    except:
        raise PermissionDenied('Authentication failed. (corrupted_user_info_retrieved)')
    # data from info is directly saved to db, this means that the appointed shen system is fully trusted
    #  this is breached when the shen server is man in the middled, but then an attacker needs to steal both the domain as well as the secret keys

    # find user and map shen user to local user
    existent_user = get_user(user.object.email, user.object.username)
    if existent_user:
        user.object.pk = existent_user.pk
        existent_usermeta = existent_user.usermeta
        usermeta.object.pk = existent_usermeta.pk
        groups = list(existent_user.groups.all())

        # for fields that do not exist on shen but do exist on local, port the value over otherwise data is lost
        for local_field in settings.USERMETA_LOCAL_FIELDS:
            setattr(usermeta.object, local_field, getattr(existent_usermeta, local_field))
        try:
            user.save()
            usermeta.object.User = user.object
            usermeta.save()
        except:
            raise PermissionDenied("Authentication failed. (user_save_failed)")
        # foreignkeys on the user to other models are wiped with this method, foreignkeys from other models to user keep working
        # has to be done after save because its an m2m relation
        for group in groups:
            user.object.groups.add(group)
        user.object.save()
    elif existent_user is None:
        # user does not exist
        user.object.pk = None
        usermeta.object.pk = None
        try:
            user.save()
            usermeta.object.User = user.object
            usermeta.save()
        except:
            raise PermissionDenied("Authentication failed. (create_new_user_failed)")
    else:
        # more then one user found with this combination, db corrupted, abort
        # this will not happen, as get_user already raises exception
        return HttpResponseNotFound()
    user = user.object
    usermeta = usermeta.object
    response = check_user(request, user)
    if response is not True:
        return response

    # login user
    auth.login(request, user)

    if next_url is not None:
        if is_safe_url(next_url, None):
            return HttpResponseRedirect(next_url)

    return HttpResponseRedirect("/")


@ensure_csrf_cookie
def login(request):
    """
    Set session cookie and redirect to shen
    :param request:
    :return:
    """
    client = WebApplicationClient(settings.SHEN_RING_CLIENT_ID)
    if not settings.SHEN_RING_NO_CSRF:
        state = request.META.get("CSRF_COOKIE", "ERROR")
    else:
        state = ""
    if request.GET.get('next', None) is not None:
        state += "-" + base64.b64encode(request.GET.get('next').encode()).decode()
    url = client.prepare_request_uri(settings.SHEN_RING_URL + "oauth/authorize/", state=state, approval_prompt='auto')
    return HttpResponseRedirect(url)

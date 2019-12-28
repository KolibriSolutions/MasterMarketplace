from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from index.decorators import group_required
from general_mail import send_mail
from general_view import get_grouptype
from projects.models import Project
from projects.utils import get_visible_projects
from studyguide.models import CapacityGroup, GroupAdministratorThrough


@login_required
def api_info(request):
    return render(request, 'api/api.html')


@group_required('studyadvisors', 'directors')
def verify_assistant(request, pk):
    """
    API call to verify an unverified assistant as a assistant.

    :param request:
    :param pk: id of the assistant-user
    :return:
    """
    account = get_object_or_404(User, pk=pk)

    if get_grouptype("unverified") not in account.groups.all():
        return HttpResponse("This account is already verified")

    if verify_assistant_fn(account):
        return HttpResponse("Account verified!")
    else:
        return HttpResponse("Verify failed!")


def verify_assistant_fn(user):
    """
    Verify an unverified user and mail a confirmation.

    :param user:
    :return:
    """
    account_group = User.groups.through.objects.get(user=user)
    account_group.group = get_grouptype("assistants")
    account_group.save()
    # inform the user of verification.
    send_mail("user groups changed", "email/user_groups_changed.html",
              {'oldgroups': 'unverified',
               'newgroups': 'assistants',
               'message': 'Your account is now verified!',
               'user': user},
              user.email)
    return True


@login_required
def list_public_projects_api(request):
    """
    Return all public proposals (=type 4) ordered by group as JSON

    :param request:
    :return: JSON response
    """
    data = {}
    projects = get_visible_projects(request.user)
    for group in CapacityGroup.objects.all():
        data[str(group)] = {
            "name": str(group),
            "projects": [prop.id for prop in projects if prop.Group == group]
        }
    return JsonResponse(data)


@login_required
def list_public_projects_titles_api(request):
    """
    Get all public proposals (=status 3) titles as JSON

    :param request:
    :return: JSON response
    """
    data = {}

    for prop in get_visible_projects(request.user):
        data[prop.id] = prop.Title

    return JsonResponse(data)


@login_required
def detail_proposal_api(request, pk):
    """
    Get detailed information of given proposal as JSON

    :param request:
    :param pk: id of the proposal
    :return:
    """
    props = get_visible_projects(request.user)
    prop = get_object_or_404(Project, pk=pk)
    if prop not in props:
        return HttpResponse("Not allowed", status=403)

    return JsonResponse({
        "id": prop.id,
        "detaillink": reverse("projects:details", kwargs={'pk': prop.id}),
        "title": prop.Title,
        "group": str(prop.Group),
        "link": prop.SiteUrl,
        "reponsible": str(prop.ResponsibleStaff),
        "assistants": [str(u) for u in list(prop.Assistants.all())],
        "generaldescription": prop.GeneralDescription,
        "taskdescription": prop.StudentsTaskDescription,
    })


@login_required
def list_published_api(request):
    """
    JSON list of all published proposals with some detail info.

    :param request:
    :return:
    """
    props = get_visible_projects(request.user)
    l = []
    for prop in props:
        l.append({
            "id": prop.id,
            "detaillink": reverse("projects:details", kwargs={'pk': prop.id}),
            "title": prop.Title,
            "group": str(prop.Group),
            "link": prop.SiteUrl,
            "reponsible": str(prop.ResponsibleStaff),
            "assistants": [str(u) for u in list(prop.Assistants.all())],
        })
    return JsonResponse(l, safe=False)


@group_required('studyadvisors', 'directors')
def get_group_admins(request, pk, type):
    group = get_object_or_404(CapacityGroup, pk=pk)

    if type == 'read':
        return JsonResponse([g.User.id for g in GroupAdministratorThrough.objects.filter(Group=group, Super=False)],
                            safe=False)
    elif type == 'write':
        return JsonResponse([g.User.id for g in GroupAdministratorThrough.objects.filter(Group=group, Super=True)],
                            safe=False)
    else:
        return HttpResponseBadRequest()

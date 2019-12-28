from datetime import datetime

from django.conf import settings
from django.core import signing
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.urls import reverse

from accesscontrol.models import AllowedAccess
from general_view import get_grouptype
from projects.models import Project, Favorite
from studyguide.models import GroupAdministratorThrough


def can_create_project_fn(user):
    """
    Check if a user can create a project. Allowed for responsible, assistant and studyadvisors
    Group administrators can create projects when they have rw access.

    :param user: user
    :return: tuple with Boolean and String.
    """
    if get_grouptype('assistants') in user.groups.all() or \
            get_grouptype('supervisors') in user.groups.all():
        return True, ''
    if get_grouptype('groupadministrator') in user.groups.all():
        if len(get_writable_admingroups(user)) != 0:
            return True, ''
        else:
            return False, "You are not allowed to create projects, you are read-only group administrator."
    return False, "You are not allowed to create new projects."


def can_edit_project_fn(user, proj):
    """
    Check if a user can edit a proposal. Used to show/hide editbuttons on detailproposal and
    for the can_edit_project decorator.

    :param user: user
    :param proj: proposal
    :return: tuple with Boolean and String.
    """
    if proj.Progress == 2:
        return False, "This project has status Finished. It cannot be changed."

    if user.is_superuser or \
            get_grouptype('studyadvisors') in user.groups.all():
        if proj.Status != 3:
            return True, ''

    gs = group_administrator_status(proj, user)
    if gs == 2:
        if proj.Status != 3:
            return True, ''
    elif gs == 1 and not (proj.ResponsibleStaff == user or user in proj.Assistants.all()):
        return False, 'You are group administrator with read only rights for this project. Editing this project is not allowed.'

    if proj.ResponsibleStaff == user or \
            user in proj.Assistants.all():
        # request.user in proj.ExternalStaff.all() or \
        # published proposals can never be edited.
        if proj.Status == 3:
            return False, "No editing possible. This project is already published. " \
                          "Please downgrade it to draft to edit."

        elif proj.Status == 2:
            if user == proj.ResponsibleStaff:
                return True, ''
            return False, "Please downgrade the project to status 1 (draft) to edit the project."
        # owners can edit proposal when in draft. Status==1
        elif proj.Status == 1:
            return True, ''

    return False, 'You are not allowed to edit this project.'


def can_downgrade_project_fn(user, proj):
    """
    Check if user can downgrade a project. upgrade is same as with can_edit_project_fn

    :param user:
    :param proj:
    :return:
    """

    if proj.Status > 1 and \
            proj.Progress is None and \
            (proj.ResponsibleStaff == user or
             get_grouptype('studyadvisors') in user.groups.all() or
             group_administrator_status(proj, user) == 2):
        return True, ""

    if proj.Status == 2 and \
            user in proj.Assistants.all():
        return True, ""

    if proj.Status == 1:
        return False, ""

    return can_edit_project_fn(user, proj)


def can_delete_project_fn(user, proj):
    """
    Whether a user can delete a project.

    :param user:
    :param proj:
    :return:
    """
    if user in proj.Assistants.all():
        return False, "Assistants of a project are not allowed to delete a project."
    p = can_edit_project_fn(user, proj)
    if p[0] is False:
        return p
    else:
        return True, ''


def can_distribute_project_fn(user, proj):
    """
    Whether a user can set distributions on a project.

    :param user:
    :param proj:
    :return:
    """
    p = can_set_progress_project_fn(user, proj)
    if p[0] is False:
        return p

    if proj.Progress == 2:
        return False, "This project has status Finished. The distributions cannot be changed."

    return True, ''


def can_set_progress_project_fn(user, proj):
    """
    Whether a user can set the progress of a project.
    Also used to check if a user can set distributions.

    :param user:
    :param proj:
    :return:
    """
    if user != proj.ResponsibleStaff and \
            not user.is_superuser and \
            group_administrator_status(proj, user) < 2 and \
            not get_grouptype('studyadvisors') in user.groups.all():
        return False, "Only responsible staff, study advisor or group administration (with write access) " \
                      "can set distributions or set progress for a project"
    if proj.Status != 3:
        return False, "To change the progress or distributions, this project needs to have status 3, active."

    return True, ''


def getStatStr(status):
    """
    returns string for proposal status change message

    :param status: integer with the status
    :return: a string with the status
    """
    allstatstr = "Project status changed to '{}'<br /><ol>".format(Project.StatusOptions[status - 1][1])
    for opt in Project.StatusOptions:
        allstatstr += "<li class=\""
        if opt[0] == status:
            allstatstr += "text-accent fg-navy"
        else:
            allstatstr += "text-secondary"
        allstatstr += "\">" + opt[1] + "</li>"
    return allstatstr + "</ol>"


def get_non_finished_projects():
    return Project.objects.exclude(Progress=2)


def get_visible_projects(user):
    """
    Get all status=3 projects that are public visible for the given user.
    ELE students can see all projects. Non-ELE students can see the projects from groups for their Origin (whitelist).
    :param user:
    :return:
    """
    active_projects = Project.objects.filter(Status=3)
    now = datetime.now().date()
    public_projects = active_projects.filter(((Q(StartDate__isnull=False) & Q(StartDate__lte=now)) |
                                              Q(StartDate__isnull=True)) &
                                             ((Q(EndDate__isnull=False) & Q(EndDate__gte=now)) |
                                              Q(EndDate__isnull=True))
                                             )

    if not user.groups.exists() and not user.is_superuser:
        access = get_object_or_404(AllowedAccess, Email=user.email)
        if access.Origin.Name == 'ELE':
            return public_projects
        else:
            return public_projects.filter(Group__in=access.Origin.Groups.all())
    else:
        return public_projects


def filter_visible_projects(projects, user):
    """
    Filter a list of projects by public_visible and user Origin

    :param projects: iterable of projects.
    :param user:
    :return:
    """
    if not user.groups.exists() and not user.is_superuser:
        access = AllowedAccess.objects.get(Email=user.email)
        if access.Origin.Name == 'ELE':
            visibleprojects = [project for project in projects if project.public_visible()]
        else:
            visibleprojects = [project for project in projects if project.public_visible()
                               and project.Group in access.Origin.Groups.all()]
    else:
        visibleprojects = [project for project in projects if project.public_visible()]
    return visibleprojects


status_filters = ['finished', 'draft', 'active', 'future']
def filter_status(projects, status_filter):
    """
    Filter projects by status

    :param projects:
    :param status_filter:
    :return:
    """
    now = datetime.now().date()
    if status_filter == 'finished':
        # either progress set to finished or end date visible reached.
        return projects.filter(Q(Progress=2) | (Q(EndDate__isnull=False) & Q(EndDate__lt=now))).distinct()
    elif status_filter == 'draft':
        return projects.filter(Status__lt=3).distinct()
    elif status_filter == 'active':
        return projects.filter(Status=3).filter(((Q(StartDate__isnull=False) & Q(StartDate__lte=now)) |
                                                  Q(StartDate__isnull=True)) &
                                                 ((Q(EndDate__isnull=False) & Q(EndDate__gte=now)) |
                                                  Q(EndDate__isnull=True))
                                                 ).distinct()
    elif status_filter == 'future':
        return projects.filter((Q(StartDate__isnull=False) & Q(StartDate__gte=now))).distinct()
    return None


def prefetch(projects):
    """
    Prefetch interesting data for a list of projects.

    :param projects:
    :return:
    """
    projects = projects.select_related('ResponsibleStaff__usermeta', 'Group'). \
        prefetch_related('Assistants__usermeta', 'Program', 'Labels', 'SecondaryGroup', 'distributions', 'applications')

    return projects


def get_favorites(user):
    """
    Get pk's of favorited projects

    :param user:
    :return:
    """
    return list(Favorite.objects.filter(User=user).values_list('Project__pk', flat=True))


def group_administrator_status(project, user):
    """
    Returns the administrator status of user for the group belonging to the project
    status 0: no admin
    status 1: read only admin
    status 2: read/write admin

    :param project:
    :param user:
    :return:
    """
    try:
        g = GroupAdministratorThrough.objects.get(Group=project.Group, User=user)
    except GroupAdministratorThrough.DoesNotExist:
        for psg in project.SecondaryGroup.all():
            try:
                gs = GroupAdministratorThrough.objects.get(Group=psg, User=user)
            except GroupAdministratorThrough.DoesNotExist:
                continue
            return 1  # groupadmin of secondary group can only view, not edit.
        return 0  # no primary and no secondary group admin

    # groupadmin of primary group, check super value.
    if g.Super:
        return 2  # rw
    else:
        return 1  # readonly


def get_writable_admingroups(user):
    """
    returns group objects for which this user is writable group admin

    :param user:
    :return:
    """
    return [g.Group for g in GroupAdministratorThrough.objects.filter(User=user, Super=True)]


def get_share_link(pk):
    """
    Create a share link for a proposal detail page.
    Used to let unauthenticated users view a proposal, possibly before the proposal is public.

    :param pk: pk of the proposal to get a link for.
    :return:
    """
    return settings.DOMAIN + reverse('projects:viewsharelink', args=[signing.dumps(pk)])

# def get_cached_project(pk):
#     """
#     Get a project from cache or from database. Put it in cache if it is not yet in cache.
#
#     :param pk: pk of project
#     :return:
#     """
#     cprop = cache.get('project_{}'.format(pk))
#     if cprop is None:
#         prop = get_object_or_404(Project, pk=pk)
#         if prop.Status == 'active':
#             cache.set('project_{}'.format(pk), prop, None)
#         return prop
#     else:
#         return cprop

#
# def update_cached_project(proj):
#     """
#     Update a cached project
#
#     :param prop: proposal object
#     :return:
#     """
#     if proj.Status == 'active':
#         cache.set('project_{}'.format(proj.id), proj, settings.STATIC_OBJECT_CACHE_DURATION)
#     else:
#
#
# def updateProjCache_pk(pk):
#     """
#     Update a cached project
#
#     :param pk: pk of project
#     :return:
#     """
#     prop = get_object_or_404(Project, pk=pk)
#     if prop.Status == 'active':
#         cache.set('project_{}'.format(pk), prop, None)

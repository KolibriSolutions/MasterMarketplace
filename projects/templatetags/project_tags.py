from django import template
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from general_view import get_all_projects
from projects.utils import can_create_project_fn, can_edit_project_fn, can_downgrade_project_fn, can_delete_project_fn, can_set_progress_project_fn, can_distribute_project_fn, group_administrator_status

register = template.Library()


@register.simple_tag
def get_pending_tag(user):
    """

    :param user:
    :return:
    """
    # <button> inside <a> is invalid HTML5. MetroUI does not work well with loading-pulse on non-button, so keep it.
    html = "<a href='" + reverse(
        "projects:pending") + "'><button class=\"button danger loading-pulse\">Pending: {}</button></a>"

    num = 0
    num += get_all_projects().filter(Status=2, ResponsibleStaff=user.pk).distinct().count()
    num += get_all_projects().filter(Status=1, Assistants__id=user.pk).distinct().count()

    if num == 0:
        return "No pending projects for your attention"
    else:
        return format_html(html.format(num))


@register.simple_tag
def is_favorite(project, user):
    return project.favorites.filter(User=user).exists()


@register.filter(name='group_administrator_status')
def group_administrator_status_tag(proj, user):
    return group_administrator_status(proj, user)


@register.filter(name='can_create_project')
def can_create_project_tag(user):
    return can_create_project_fn(user)[0]


@register.filter(name='can_edit_project')
def can_edit_project_tag(project, user):
    return can_edit_project_fn(user, project)[0]


@register.filter(name='can_downgrade_project')
def can_downgrade_project_tag(project, user):
    return can_downgrade_project_fn(user, project)[0]


@register.filter(name='can_delete_project')
def can_delete_project_tag(project, user):
    return can_delete_project_fn(user, project)[0]


@register.filter(name='can_set_progress_project')
def can_set_progress_project_tag(project, user):
    return can_set_progress_project_fn(user, project)[0]


@register.filter(name='can_distribute_project')
def can_distribute_project(project, user):
    return can_distribute_project_fn(user, project)[0]


@register.filter(name='project_labels')
def project_labels(project):
    html_span = '<span class="project_label {}">{}</span>'
    html_str = ""
    for label in project.Labels.all():
        html_str += html_span.format(label.Color, label.Name)

    return mark_safe(html_str)

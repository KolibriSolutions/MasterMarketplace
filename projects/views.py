from itertools import chain

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core import signing
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.db.models import Q, Sum, Count
from django.forms import modelformset_factory
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from render_block import render_block_to_string

from accesscontrol.models import Origin
from general_form import ConfirmForm
from general_mail import mail_project_all, send_mail
from general_model import print_list, delete_object
from general_view import get_grouptype, get_all_projects
from index.decorators import group_required
from projects import check_content_policy
from projects.decorators import can_view_project, can_edit_project, can_downgrade_project, can_create_project, can_delete_project, can_distribute_project, can_set_progress_project
from projects.utils import getStatStr, get_share_link, can_edit_project_fn, get_favorites
from students.models import Distribution
from studyguide.models import CapacityGroup, MasterProgram
from tracking.models import ProjectStatusChange, DistributionTracking
from tracking.utils import get_ProjectTracking, tracking_visit_project
from .forms import ProjectFormEdit, ProjectFormCreate, ProjectImageForm, ProjectDowngradeMessageForm, \
    ProjectAttachmentForm, DistributionForm, ProgressForm, ProjectLabelForm
from .models import Project, ProjectImage, ProjectAttachment, ProjectLabel
from .utils import get_visible_projects, group_administrator_status, prefetch, filter_status, status_filters, get_non_finished_projects


@login_required
def list_public_projects(request, type_filter=None):
    """
    List all the public projects. This is the overview for students to choose a project from.

    :param request:
    :param type_filter: optional filter projects on graduation or internship.
    :return:
    """

    if get_grouptype('unverified') in request.user.groups.all():
        raise PermissionDenied("You are not allowed to view the project list, "
                               "because your account is not yet verified.")

    visible_projects = get_visible_projects(request.user)
    if type_filter:
        if type_filter in ['graduation', 'internship']:
            visible_projects = visible_projects.filter(Q(Type=type_filter) | Q(Type='both')).distinct()
        else:
            raise PermissionDenied('Invalid filter applied!')

    visible_projects = visible_projects.select_related('ResponsibleStaff__usermeta', 'Group'). \
        prefetch_related('Assistants__usermeta', 'Program', 'Labels', 'SecondaryGroup')

    favorite_projects = get_favorites(request.user)

    return render(request, 'projects/list_projects.html', {
        'projects': visible_projects,
        'favorite_projects': favorite_projects,
        'type_filter': type_filter,
    })


@login_required
def list_favorite_projects(request, type_filter=None):
    """
    List all the projects a student has favorited, this view is not cached

    :param request:
    :param type_filter: optional filter projects on graduation or internship.
    :return:
    """
    projects = get_visible_projects(request.user).filter(favorites__User=request.user)
    if type_filter:
        if type_filter in ['graduation', 'internship']:
            projects = projects.filter(Q(Type=type_filter) | Q(Type='both')).distinct()
        else:
            raise PermissionDenied('Invalid filter applied!')
    projects = projects.select_related('ResponsibleStaff__usermeta', 'Group'). \
        prefetch_related('Assistants__usermeta', 'Program', 'Labels', 'SecondaryGroup')

    return render(request, 'projects/list_projects.html', {
        'projects': projects,
        'favorite_projects': get_favorites(request.user),
        'favorite': True,
        'type_filter': type_filter,
    })


@group_required('supervisors', 'assistants', 'studyadvisors')  # external
def list_own_projects(request, status_filter=None):
    """
    This lists all projects that the given user has something to do with. Either a responsible or assistant. For
    Type3staff this lists all projects. This is the ussual view for staff to view their projects.

    :param request:
    :param status_filter: status to filter on
    :return:
    """
    if not status_filter:
        status_filter = 'active'
    if status_filter not in status_filters:
        raise PermissionDenied("Invalid filter applied.")
    if get_grouptype("studyadvisors") in request.user.groups.all() or request.user.is_superuser:
        projects = Project.objects.all()
    else:
        projects = Project.objects.filter(Q(ResponsibleStaff=request.user) |
                                          Q(Assistants=request.user)
                                          ).distinct()
    projects = filter_status(projects, status_filter)
    projects = prefetch(projects)
    return render(request, 'projects/list_projects_custom.html', {
        'hide_sidebar': True,
        'projects': projects,
        'favorite_projects': get_favorites(request.user),
        'status_filter': status_filter,
        'status_filters': status_filters,
    })


@group_required('groupadministrator')
def list_group_projects(request, status_filter=None):
    """
    List all proposals of a group.

    :param request:
    :param status_filter: status to filter on
    :return:
    """
    if not status_filter:
        status_filter = 'active'
    if status_filter not in status_filters:
        raise PermissionDenied("Invalid filter applied.")
    adminsgroups = request.user.administratoredgroups.all().values_list('Group', flat=True)
    projects = Project.objects.filter(Q(Group__Administrators=request.user) |
                                      Q(SecondaryGroup__in=adminsgroups)
                                      ).distinct()
    projects = filter_status(projects, status_filter)
    projects = prefetch(projects).distinct()
    return render(request, 'projects/list_projects_custom.html', {
        'hide_sidebar': True,
        'projects': projects,
        'favorite_projects': get_favorites(request.user),
        'title': '{} projects of {}'.format(status_filter, print_list(request.user.administratoredgroups.all().values_list('Group__ShortName', flat=True))),
        'status_filters': status_filters,
        'status_filter': status_filter,
    })


@can_view_project
def detail_project(request, pk):
    """
    Detailview page for a given project. Displays all information for the project. Used for students to choose a
    project from, and for staff to check. For staff it shows edit and up/downgrade buttons. For students it shows a
    apply or retract button if application method is set to this system.
    buttons are inserted using a .format() on {} in the template.

    :param request:
    :param pk: pk of the project
    :return:
    """
    proj = get_object_or_404(Project.objects.
                             select_related('ResponsibleStaff', 'Group__Head').
                             prefetch_related('Assistants', 'images', 'attachments', 'Program',
                                              'RecommendedCourses'), pk=pk)

    # if student
    if not request.user.groups.exists():
        if proj.distributions.filter(Student=request.user).exists():
            if proj.Progress:
                button = 'You are distributed to this project. The project progress is set to <i>{}</i>.'.format(proj.ProgressOptions[proj.Progress - 1][1])
            else:
                button = 'You are distributed to this project. The project status is set to <i>{}</i>.'.format(proj.StatusOptions[proj.Status - 1][1])
        else:
            # make apply / retract button.
            if proj.Progress == 2:  # Project is finished
                button = 'It is not possible to apply to this project, as it has its progress set to Finished.'
            elif proj.Progress == 3:
                button = 'It is not possible to apply to this project, as it is set to reserved.'
            else:
                if proj.Apply == 'system':
                    button = '<a href="{}" class="button {}">{}</a>'
                    if request.user.applications.filter(Project=proj).exists():  # if user has applied to this project
                        button = button.format(reverse('students:retractapplication',
                                                       args=[request.user.applications.filter(Project=proj)[0].id]),
                                               'danger',
                                               'Retract Application')
                    else:  # show apply button
                        button = button.format(reverse('students:confirmapply', args=[proj.id]), 'primary', 'Apply')
                else:
                    button = 'Apply to this project by contacting the supervisor.'

        data = {"project": proj,
                "user": request.user
                }
        cdata = render_block_to_string("projects/detail_project.html", 'body', data)
        tracking_visit_project(proj, request.user)
        return render(request, "projects/detail_project.html", {"bodyhtml": cdata.format(button), 'project': proj})

    # if staff:
    else:
        e = can_edit_project_fn(request.user, proj)
        ps = list(MasterProgram.objects.all())
        os = list(Origin.objects.all())
        pt = get_ProjectTracking(proj)
        counts_reg = [pt.UniqueVisitors.filter(registration__Program=p).count() for p in ps]
        counts_origin = [pt.UniqueVisitors.filter(allowedaccess__Origin=o).count() for o in os]
        stat = {'labels_reg': [p.__str__() for p in ps], 'counts_reg': counts_reg,
                'labels_origin': [o.__str__() for o in os], 'counts_origin': counts_origin}
        return render(request, "projects/detail_project.html", {
            "project": proj,
            'cpv': cache.get('cpv_proj_{}'.format(proj.pk)),  # if not cached, ignore cpv
            'stat': stat,
            'edit_lock': False if e[0] else e[1]
        }
                      )


@can_create_project
def create_project(request):
    """
    Create a new project. Only for staff.

    :param request:
    :return:
    """
    if request.method == 'POST':
        form = ProjectFormCreate(request.POST, request=request)
        if form.is_valid():
            proj = form.save(commit=True)
            mail_project_all(request, proj)
            return render(request, "projects/message_project.html", {"Message": "Project created!", "Project": proj})
    else:
        init = {}
        if get_grouptype("supervisors") in request.user.groups.all():
            init["ResponsibleStaff"] = request.user.id
        # elif get_grouptype("external") in request.user.groups.all():
        #     init["ExternalStaff"] = [request.user.id]
        elif get_grouptype("assistants") in request.user.groups.all():
            init["Assistants"] = [request.user.id]
        form = ProjectFormCreate(request=request, initial=init)
    return render(request, 'GenericForm.html', {'form': form,
                                                'formtitle': 'Create new Project',
                                                'buttontext': 'Create and go to next step'})


@can_edit_project
def edit_project(request, pk):
    """
    Edit a given project. Only for staff that is allowed to edit the project.

    :param request:
    :param pk: pk of the project to edit.
    :return:
    """
    obj = get_object_or_404(Project, pk=pk)
    if request.method == 'POST':
        form = ProjectFormEdit(request.POST, request.FILES, request=request, instance=obj)
        if form.is_valid():
            if form.changed_data:
                cache.delete('cpv_proj_{}'.format(obj.pk))
                check_content_policy.CPVCheckThread(obj).start()
            obj = form.save()
            return render(request, "projects/message_project.html", {"Message": "Project saved!", "Project": obj})
    else:
        form = ProjectFormEdit(request=request, instance=obj)
    return render(request, 'GenericForm.html', {'form': form, 'formtitle': 'Edit Project', 'buttontext': 'Save'})


@can_view_project
@can_create_project
def copy_project(request, pk):
    """
    Copy a proposal from a previous timeslot. Only for staff that is allowed to see the proposal to copy.
    This function is not visible yet, the buttons are nowhere shown.

    :param pk: the id of proposal to copy
    :param request:
    :return:
    """
    if request.method == 'POST':
        form = ProjectFormCreate(request.POST, request=request)
        if form.is_valid():
            prop = form.save()

            return render(request, "projects/message_project.html", {"Message": "Project created!", "Project": prop})
    else:
        old_proposal = get_object_or_404(Project, pk=pk)
        oldpk = old_proposal.pk
        old_proposal.pk = None
        # Assistants and privates are removed, because m2m is not copied in this way.
        form = ProjectFormCreate(request=request, instance=old_proposal, copy=oldpk)
    return render(request, 'GenericForm.html', {'form': form,
                                                'formtitle': 'Edit copied project',
                                                'buttontext': 'Create and go to next step'})


@can_edit_project
def add_file(request, pk, ty):
    """
    Add a file of type ty to a project. The type can be an image or a file (usually pdf). The image is shown in an
    image slider, an attachment is shown as a download button.

    :param request:
    :param pk: pk of the project
    :param ty: type of file to add. i for image, a for attachment
    :return:
    """
    obj = get_object_or_404(Project, pk=pk)
    if ty == "i":
        ty = "image"
        form = ProjectImageForm
    elif ty == "a":
        ty = "attachment"
        form = ProjectAttachmentForm
    else:
        raise PermissionDenied("Invalid type supplied")

    if request.method == 'POST':
        form = form(request.POST, request.FILES, request=request)
        if form.is_valid():
            file = form.save(commit=False)
            file.Project = obj
            file.save()
            return render(request, "projects/message_project.html",
                          {"Message": "File to Project saved! Click the button below to add another file.",
                           "Project": obj})

    return render(request, 'GenericForm.html',
                  {'form': form, 'formtitle': 'Add ' + ty + ' to project ' + obj.Title, 'buttontext': 'Save'})


@can_edit_project
def edit_file(request, pk, ty):
    """
    Edit a file of a project.

    :param request:
    :param pk: pk of the project to edit file of
    :param ty: type of file to edit, either i for image or a for attachement
    :return:
    """
    obj = get_object_or_404(Project, pk=pk)
    if ty == "i":
        ty = "image"
        model = ProjectImage
        form = ProjectImageForm
    elif ty == "a":
        ty = "attachment"
        model = ProjectAttachment
        form = ProjectAttachmentForm
    else:
        raise PermissionDenied("Invalid type supplied")

    form_set = modelformset_factory(model, form=form, can_delete=True, extra=0)
    qu = model.objects.filter(Project=obj)

    formset = form_set(queryset=qu)

    if request.method == 'POST':
        formset = form_set(request.POST, request.FILES)
        if formset.is_valid():
            formset.save()
            return render(request, "projects/message_project.html",
                          {"Message": "File changes saved!", "Project": obj})
    return render(request, 'GenericForm.html',
                  {'formset': formset, 'formtitle': 'All ' + ty + 's in project ' + obj.Title, "Project": obj.pk,
                   'buttontext': 'Save changes'})


@can_delete_project
def ask_delete_project(request, pk):
    """
    A confirmform for supervisors to delete a project. Regular staff cannot delete a project, as this should not
    happen. Public (=status4) projects cannot be deleted.

    :param request:
    :param pk: pk of project to delete.
    :return:
    """
    obj = get_object_or_404(Project, pk=pk)
    form = "<a href=" + reverse('projects:deleteproject', kwargs={"pk": int(
        pk)}) + " class='button warning'><span class='mif-bin'></span>click here to DELETE</a></button></form>"
    return render(request, "projects/message_project.html",
                  {"Message": "Are you sure to delete? This cannot be undone " + form, "Project": obj})


@can_delete_project
def delete_project(request, pk):
    """
    Really delete a project. This can only be called by supervisor after going to the confirm delete page.

    :param request:
    :param pk: pk of the project to delete
    :return:
    """
    obj = get_object_or_404(Project, pk=pk)
    if "HTTP_REFERER" in request.META:
        if 'ask' in request.META['HTTP_REFERER']:
            # make sure previous page is askdelete
            title = obj.Title
            delete_object(obj)
            return render(request, "projects/message_project.html",
                          {"Message": "Project " + title + " is removed", "return": ""})
    raise PermissionDenied("You should not access this page directly")


@can_edit_project
def upgrade_status(request, pk):
    """
    increase the status of a project.

    :param request:
    :param pk: id of project
    :return:
    """
    obj = get_object_or_404(Project, pk=pk)

    # Status 3 is not allowed in can_edit_proposal

    if obj.Status == 2:
        obj.Status = 3
        obj.save()
        mail_project_all(request, obj)

        notification = ProjectStatusChange()
        notification.Subject = obj
        notification.Actor = request.user
        notification.StatusFrom = 2
        notification.StatusTo = 3
        notification.save()

    elif obj.Status == 1:
        obj.Status = 2
        obj.save()
        mail_project_all(request, obj)

        notification = ProjectStatusChange()
        notification.Subject = obj
        notification.Actor = request.user
        notification.StatusFrom = 1
        notification.StatusTo = 2
        notification.save()
    else:
        raise PermissionDenied("This project cannot be upgraded.")

    return render(request, "projects/message_project.html",
                  context={"Message": getStatStr(obj.Status), "Project": obj})


@can_downgrade_project
@group_required('supervisors', 'assistants', 'studyadvisors', 'groupadministrator')  # external
def downgrade_status(request, pk):
    """
    Decrease the status of a project. Access control with can_view_proposal because has to work in status=3

    :param request:
    :param pk: id of project
    :return:
    """

    obj = get_object_or_404(Project, pk=pk)

    if request.method == "POST":
        form = ProjectDowngradeMessageForm(request.POST)
        if form.is_valid():
            message = form.cleaned_data['Message']
            # responsible and groupadministrator can downgrade from 3 to 2.
            if obj.Status == 3 and \
                    (request.user == obj.ResponsibleStaff or group_administrator_status(obj, request.user) == 2 or request.user.is_superuser):
                obj.Status = 2
                obj.save()
                mail_project_all(request, obj, message)

                notification = ProjectStatusChange()
                notification.Subject = obj
                notification.Message = message
                notification.Actor = request.user
                notification.StatusFrom = 3
                notification.StatusTo = 2
                notification.save()
                return render(request, "projects/message_project.html", {"Message": getStatStr(obj.Status), "Project": obj})
            elif obj.Status == 2:
                obj.Status = 1
                obj.save()
                mail_project_all(request, obj, message)

                notification = ProjectStatusChange()
                notification.Subject = obj
                notification.Message = message
                notification.Actor = request.user
                notification.StatusFrom = 2
                notification.StatusTo = 1
                notification.save()
                return render(request, "projects/message_project.html", {"Message": getStatStr(obj.Status), "Project": obj})
            else:
                raise PermissionDenied("You are not allowed to downgrade status.")
    else:
        form = ProjectDowngradeMessageForm()
        return render(request, 'GenericForm.html',
                      {'form': form, 'formtitle': 'Message for downgrade project ' + obj.Title,
                       'buttontext': 'Downgrade and send message'})


@group_required('supervisors', 'assistants', 'groupadministrator')  # external
def list_pending(request):
    """
    Get and show the pending projects for a given user.

    :param request:
    :return:
    """

    props = []
    if get_grouptype("assistants") in request.user.groups.all():
        props = get_all_projects().filter(Q(Assistants__id=request.user.id) & Q(Status__exact=1)).distinct()
    elif get_grouptype("supervisors") in request.user.groups.all():
        # group supervisor can also be assistant of a project.
        props = get_all_projects().filter((Q(Assistants__id=request.user.id) & Q(Status__exact=1)) |
                                          (Q(ResponsibleStaff=request.user.id) & Q(Status__lte=2))).distinct()
    props = list(props)

    if get_grouptype('groupadministrator') in request.user.groups.all() and request.user.administratorgroups.exists():
        for group in request.user.administratorgroups.all():
            props = set(list(chain(props, list(get_all_projects().filter(Q(Group=group) & Q(Status__lte=2))))))
        title = 'Pending projects for your group'
    else:
        title = 'Pending projects'
    return render(request, "projects/list_projects_custom.html", {"projects": props, "title": title})


@can_view_project
@group_required('supervisors', 'assistants', 'studyadvisors', 'groupadministrator')  # external
def share(request, pk):
    """
    Get a sharelink for a given project. This link is a public view link for a project-detailpage
    The link is valid as long as the project is public visible.
v
    :param request:
    :param pk: Project pk to get sharelink for
    :return:
    """

    link = get_share_link(pk)
    return render(request, "base.html", {
        "Message": "Share link created: <a href=\"{}\">{}</a> <br/>"
                   " Use this to show the project to anybody outside the marketplace. "
                   "The link is valid as long as this project is public visible".format(link, link),
    })


def view_share_link(request, token):
    """
    Translate a given sharelink to a project detailpage. Public (world) visible

    :param request:
    :param token: sharelink token, which includes the pk of the project
    :return: project detail render
    """
    try:
        pk = signing.loads(token)
    except:
        return render(request, "base.html",
                      context={"Message": "Invalid share link token."},
                      )
    obj = get_object_or_404(Project, pk=pk)
    if obj.public_visible():
        return render(request, "projects/detail_project.html", {"project": obj})
    else:
        raise PermissionDenied("This project is no longer visible.")


@can_distribute_project
def distribute_project(request, pk):
    proj = get_object_or_404(Project, pk=pk)

    # init = {'Students':[s.Student.pk for s in proj.distributions.all()]}
    init = {'Students': User.objects.filter(distributions__Project=proj)}
    if request.method == 'POST':
        form = DistributionForm(request.POST, initial=init)
        if form.is_valid():
            students = list(form.cleaned_data['Students'])
            for d in proj.distributions.all():
                if d.Student in students:
                    # student already distributed. Re-save to link possible new application
                    students.remove(d.Student)
                    d.save()
                else:
                    # student undistributed
                    mailcontext = {
                        'project': proj,
                        'message': "Your distribution was removed from project:"
                    }
                    send_mail("project undistributed", "email/project_distributed_email.html",
                              mailcontext, d.Student.email)
                    d.delete()
                    track = DistributionTracking()
                    track.Project = proj
                    track.Student = d.Student
                    track.Type = 'u'
                    track.save()
            for s in students:
                # new distribution
                d = Distribution(Student=s, Project=proj)
                d.save()
                mailcontext = {
                    'project': proj,
                    'message': "You are distributed to the following project:"
                }
                send_mail("project distributed", "email/project_distributed_email.html",
                          mailcontext, s.email)
                track = DistributionTracking()
                track.Project = proj
                track.Student = d.Student
                track.Type = 'd'
                track.save()
            return render(request, "base.html",
                          {"Message": "Distributions saved and student(s) notified!  <br />"
                                      "<a class='button info' href='" +
                                      reverse("projects:progress", kwargs={'pk': pk}) +
                                      "'> Set the progress of this project</a>",
                           'return': "projects:details", 'returnget': pk})
    else:
        form = DistributionForm(initial=init)

    return render(request, 'projects/ProjectDistributionForm.html',
                  {'form': form,
                   'formtitle': "Distribute students to project {}".format(proj.__str__()),
                   'buttontext': 'Save',
                   'project': proj,
                   'applications': proj.applications.all(),
                   })


@can_set_progress_project
def progress_project(request, pk):
    proj = get_object_or_404(Project, pk=pk)
    if request.method == 'POST':
        form = ProgressForm(request.POST, instance=proj)
        if form.is_valid():
            form.save()
            return render(request, "base.html",
                          {"Message": "Progress saved!  <br />",
                           'return': "projects:chooseedit"})
    else:
        form = ProgressForm(instance=proj)

    return render(request, 'GenericForm.html',
                  {'form': form, 'formtitle': "Set progress of project {}".format(proj.__str__()),
                   'buttontext': 'Save'})


@group_required('studyadvisors', 'directors', 'supervisors', 'assistants', 'groupadministrator')
def list_labels(request):
    """
    List project labels

    :param request:
    :return:
    """
    labels = ProjectLabel.objects.all()
    return render(request, 'projects/list_labels.html', {
        'labels': labels,
        'support_name': settings.SUPPORT_NAME,
        'support_role': settings.SUPPORT_ROLE,
    })


@group_required('studyadvisors', 'directors', 'supervisors', 'assistants', 'groupadministrator')
def add_label(request):
    """
    Create labels

    :param request:
    :return:
    """
    if request.method == 'POST':
        form = ProjectLabelForm(request.POST)
        if form.is_valid():
            obj = form.save()
            if get_grouptype('studyadvisors') in request.user.groups.all():
                obj.Active = True
                obj.save()
                return render(request, 'base.html', {"Message": "Active label saved!", "return": "projects:labels"})
            return render(request, 'base.html', {"Message": "Inactive label saved!", "return": "projects:labels"})
    else:
        form = ProjectLabelForm()
    return render(request, 'projects/label_form.html',
                  {'form': form, 'formtitle': 'Project Label', 'buttontext': 'Save',
                   'label': {"Name": "Placeholder text", "Color": None}})


@group_required('studyadvisors', 'directors')
def edit_label(request, pk):
    """
    Edit label

    :param request:
    :param pk: pk of label
    :return:
    """
    obj = get_object_or_404(ProjectLabel, pk=pk)
    if request.method == 'POST':
        form = ProjectLabelForm(request.POST, instance=obj)
        if form.is_valid():
            obj = form.save()
            # set to active when support user edits object
            obj.Active = True
            obj.save()
            return render(request, 'base.html', {"Message": "Label saved and activated!", "return": "projects:labels"})
    else:
        form = ProjectLabelForm(instance=obj)
    return render(request, 'projects/label_form.html',
                  {'form': form, 'formtitle': 'Project Label', 'buttontext': 'Save', 'label': obj})


@group_required('studyadvisors', 'directors')
def activate_label(request, pk):
    """
    Set label to active

    :param request:
    :param pk: pk of label
    :return:
    """
    obj = get_object_or_404(ProjectLabel, pk=pk)
    obj.Active = True
    obj.save()
    return render(request, 'base.html', {'Message': "Label activated!", 'return': 'projects:labels'})


@group_required('studyadvisors', 'directors')
def delete_label(request, pk):
    """
    Delete label

    :param request:
    :param pk: pk of label
    :return:
    """
    obj = get_object_or_404(ProjectLabel, pk=pk)
    if request.method == "POST":
        form = ConfirmForm(request.POST)
        if form.is_valid():
            delete_object(obj)
            return render(request, 'base.html', {'Message': "Label removed!", 'return': 'projects:labels'})
    else:
        form = ConfirmForm()
    return render(request, 'GenericForm.html', {
        'form': form,
        'formtitle': 'Are you sure to remove label {}'.format(obj.Name),
        'buttontext': 'Delete',
    })


@group_required('studyadvisors', 'directors', 'supervisors', 'assistants', 'groupadministrator')
def project_stats(request, status_filter=None):
    if not status_filter:
        status_filter = 'active'
    if status_filter not in status_filters:
        raise PermissionDenied("Invalid filter applied.")
    p = filter_status(Project.objects.all(), status_filter)

    totalnum = p.count()

    groups = CapacityGroup.objects.all()
    group_count = []
    group_count_distr = []
    group_count_view = []
    group_labels = []
    for group in groups:
        group_count.append(p.filter(Group=group).count())
        group_labels.append(str(group))
        group_count_distr.append(
            p.filter(Group=group, distributions__isnull=False).count())  # not distinct because users.
        group_count_view.append(p.filter(Group=group).annotate(Count('tracking__UniqueVisitors')).aggregate(Sum('tracking__UniqueVisitors__count'))['tracking__UniqueVisitors__count__sum'] or 0)
    group_labels_distr = group_labels
    group_labels_view = group_labels
    if group_count:
        group_count, group_labels = (list(t) for t in zip(*sorted(zip(group_count, group_labels), reverse=True)))
    if group_count_distr:
        group_count_distr, group_labels_distr = (list(t) for t in
                                                 zip(*sorted(zip(group_count_distr, group_labels_distr), reverse=True)))
    if group_count_view:
        group_count_view, group_labels_view = (list(t) for t in
                                               zip(*sorted(zip(group_count_view, group_labels_view), reverse=True)))

    # status_count = []
    # status_labels = []
    # for option in Project.StatusOptions:
    #     status_count.append(p.filter(Status=option[0]).count())
    #     status_labels.append(option[1])
    # if status_count:
    #     status_count, status_labels = (list(t) for t in zip(*sorted(zip(status_count, status_labels), reverse=True)))

    apply_count = []
    apply_labels = []
    for option in Project.ApplyOptions:
        apply_count.append(p.filter(Apply=option[0]).count())
        apply_labels.append(option[1])
    if apply_count:
        apply_count, apply_labels = (list(t) for t in zip(*sorted(zip(apply_count, apply_labels), reverse=True)))

    progress_count = []
    progress_labels = []
    for option in Project.ProgressOptions:
        progress_count.append(p.filter(Progress=option[0]).count())
        progress_labels.append(option[1])
    if progress_count:
        progress_count, progress_labels = (list(t) for t in
                                           zip(*sorted(zip(progress_count, progress_labels), reverse=True)))

    type_count = []
    type_labels = []
    for option in Project.TypeOptions:
        type_count.append(p.filter(Type=option[0]).count())
        type_labels.append(option[1])
    if type_count:
        type_count, type_labels = (list(t) for t in zip(*sorted(zip(type_count, type_labels), reverse=True)))

    return render(request, 'projects/stats_project.html', {
        'num': totalnum,
        # 'done': p.filter(Approved=True).count(),
        'filters': status_filters,
        'filter': status_filter,
        "mincapacity": p.aggregate(Sum('NumStudentsMin'))['NumStudentsMin__sum'],
        "maxcapacity": p.aggregate(Sum('NumStudentsMax'))['NumStudentsMax__sum'],
        'data': [
            {
                'label': 'Projects by capacity group',
                'labels': group_labels,
                'counts': group_count,
                'total': sum(group_count),
            }, {
                'label': 'Distributions by capacity group',
                'labels': group_labels_distr,
                'counts': group_count_distr,
                'total': sum(group_count_distr),
            }, {
                'label': 'Unique student views of projects',
                'labels': group_labels_view,
                'counts': group_count_view,
                'total': sum(group_count_view),
            }, {
                #     'label': 'Master program',
                #     'labels': program_labels,
                #     'counts': program_count,
                #     'total': totalnum,
                # }, {
                #     'label': 'Status options',
                #     'labels': status_labels,
                #     'counts': status_count,
                #     'total': sum(status_count),
                # }, {
                'label': 'Apply options',
                'labels': apply_labels,
                'counts': apply_count,
                'total': sum(apply_count),
            }, {
                'label': 'Progress',
                'labels': progress_labels,
                'counts': progress_count,
                'total': sum(progress_count),
            }, {
                'label': 'Type',
                'labels': type_labels,
                'counts': type_count,
                'total': sum(type_count),
            }
        ],
    })


@group_required('studyadvisors', 'directors', 'supervisors', 'assistants', 'groupadministrator')
def project_stats_personal(request):
    p = get_visible_projects(request.user)  # returns all visible projects as long as user is staff member.
    ps = list(MasterProgram.objects.all())
    os = list(Origin.objects.all())
    stats = []
    for project in p:
        pt = get_ProjectTracking(project)
        counts_reg = [pt.UniqueVisitors.filter(registration__Program=p).count() for p in ps]
        counts_origin = [pt.UniqueVisitors.filter(allowedaccess__Origin=o).count() for o in os]
        stats.append({'project': project,
                      'labels_reg': [p.__str__() for p in ps], 'counts_reg': counts_reg,
                      'labels_origin': [o.__str__() for o in os], 'counts_origin': counts_origin})
    return render(request, "projects/stats_personal_project.html", {
        'stats': stats,
    })


@group_required('studyadvisors', 'directors')
def content_policy_calc(request):
    """
    List of proposal description/assignment texts that do not met the expected text.
    Example of a policy violation is an email address in a proposal description.

    :param request:
    """
    projects = get_non_finished_projects()
    check_content_policy.CPVCheckThread(projects).start()
    return render(request, "projects/cpv_progress.html")


@group_required('studyadvisors', 'directors')
def content_policy_view(request):
    results = []
    for pk in get_non_finished_projects().values_list('pk', flat=True):
        c = cache.get('cpv_proj_{}'.format(pk))
        if c:
            results.append(c)
    return render(request, 'projects/content_policy_violations.html', {
        'pattern_policies': check_content_policy.content_policies,
        'length_requirements': check_content_policy.length_requirements.items(),
        'results': results,
    })

import base64
import json
import logging
from datetime import date, datetime

from django.contrib.auth.models import Group, User
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Sum
from django.db.models import Q
from django.forms import modelformset_factory
from django.shortcuts import get_object_or_404, render, redirect

from general_form import ConfirmForm
from general_mail import EmailThreadTemplate, send_mail
from general_model import print_list, delete_object
from general_view import get_all_staff, get_grouptype
from index.decorators import group_required
from index.models import UserMeta
from projects.utils import get_non_finished_projects
from students.utils import get_distributions
from studyguide.forms import MenuLinkForm
from studyguide.models import GroupAdministratorThrough, MenuLink
from .forms import ChooseMailingList, PromotionForm, GroupadministratorEdit, UserGroupsForm
from .models import Promotion, mail_staff_options, mail_student_options, MailTemplate, Mailing

logger = logging.getLogger('django')


#########
# Mailing#
#########

@group_required('studyadvisors', 'directors')
def list_mailing_templates(request):
    return render(request, 'support/list_mail_templates.html', {'templates': MailTemplate.objects.all()})


@group_required('studyadvisors', 'directors')
def delete_mailing_template(request, pk):
    """

    :param request:
    :param pk: pk of template
    :return:
    """
    name = 'Mailing template'
    obj = get_object_or_404(MailTemplate, pk=pk)
    if request.method == 'POST':
        form = ConfirmForm(request.POST)
        if form.is_valid():
            delete_object(obj)
            return render(request, 'base.html', {
                'Message': '{} deleted.'.format(name),
                'return': 'support:mailingtemplates'})
    else:
        form = ConfirmForm()
    return render(request, 'GenericForm.html', {
        'form': form,
        'formtitle': 'Delete {}?'.format(name),
        'buttontext': 'Delete'
    })


@group_required('studyadvisors', 'directors')
def mailing(request, pk=None):
    """
    Mailing list to mail users.

    :param request:
    :param pk: optional key of a mailing template
    :return:
    """
    if request.method == 'POST':
        form = ChooseMailingList(request.POST, staff_options=mail_staff_options, student_options=mail_student_options, )
        if form.is_valid():
            recipients_staff = set()
            recipients_students = set()
            # staff
            if form.cleaned_data['SaveTemplate']:
                t = MailTemplate(
                    RecipientsStaff=json.dumps(form.cleaned_data['Staff']),
                    RecipientsStudents=json.dumps(form.cleaned_data['Students']),
                    Message=form.cleaned_data['Message'],
                    Subject=form.cleaned_data['Subject'],
                )
                t.save()

            ts = form.cleaned_data['Year']
            for s in form.cleaned_data['Staff']:
                try:
                    # staff selected by group
                    recipients_staff.update(Group.objects.get(name=s).user_set.all())
                    if s not in ['studyadvisors', 'directors', 'groupadministrator']:
                        # if user group is not a support type, mail only users with project in this year.
                        now = datetime.now().date()
                        for staff in list(recipients_staff):
                            if not staff.projectsresponsible.exclude(Q(Progress=2) | (Q(EndDate__isnull=False) & Q(EndDate__lt=now))).exists() and not \
                                    staff.projects.exclude(Q(Progress=2) | (Q(EndDate__isnull=False) & Q(EndDate__lt=now))).exists():
                                # user has no active projects.
                                recipients_staff.remove(staff)
                except Group.DoesNotExist:
                    # not a group object, staff selected by custom options.
                    projs = get_non_finished_projects()
                    if s == 'staffdraftproj':
                        for proj in projs.filter(Status__lt=3).distinct():
                            recipients_staff.add(proj.ResponsibleStaff)
                            recipients_staff.update(proj.Assistants.all())
                    elif s == 'distributedstaff':
                        for proj in projs.filter(distributions__isnull=False).distinct():
                            recipients_staff.add(proj.ResponsibleStaff)
                            recipients_staff.update(proj.Assistants.all())
                    elif s == 'staffnostudents':
                        for proj in projs.filter(distributions__isnull=True).distinct():
                            recipients_staff.add(proj.ResponsibleStaff)
                            recipients_staff.update(proj.Assistants.all())

            # students
            students = User.objects.filter(
                Q(usermeta__Cohort=ts) &
                Q(groups=None))
            for s in form.cleaned_data['Students']:
                if s == 'all':
                    recipients_students.update(students)
                elif s == 'registered':
                    recipients_students.update(students.filter(registration__isnull=False))
                elif s == 'not-registered':
                    recipients_students.update(students.filter(Q(registration__isnull=True) & Q(usermeta__Department='ELE')).distinct())
                elif s == 'not-logged-in':
                    raise NotImplementedError()
                #     AllowedAccess.objects.filter(User__isnull=True)  # allowed access without user attached is not-logged-in user.
                #     recipients_students
                elif s == 'distributed':
                    recipients_students.update(students.filter(
                        distributions__isnull=False).distinct())

            # always send copy to admins
            for user in User.objects.filter(is_superuser=True):
                recipients_staff.add(user)
            # always send copy to self
            if request.user not in recipients_students or \
                    request.user not in recipients_staff:
                recipients_staff.update([request.user])

            mailing_obj = Mailing(
                Subject=form.cleaned_data['Subject'],
                Message=form.cleaned_data['Message'],
            )
            mailing_obj.save()
            mailing_obj.RecipientsStaff.set(recipients_staff)
            mailing_obj.RecipientsStudents.set(recipients_students)
            context = {
                'form': ConfirmForm(initial={'confirm': True}),
                'template': form.cleaned_data['SaveTemplate'],
                'mailing': mailing_obj,
            }
            return render(request, "support/email_confirm.html",
                          context=context)
    else:
        initial = None
        if pk:
            template = get_object_or_404(MailTemplate, pk=pk)
            initial = {
                'Message': template.Message,
                'Subject': template.Subject,
                'Staff': json.loads(template.RecipientsStaff),
                'Students': json.loads(template.RecipientsStudents),
            }
        form = ChooseMailingList(initial=initial, staff_options=mail_staff_options, student_options=mail_student_options)
    return render(request, "GenericForm.html", {
        "form": form,
        "formtitle": "Send mailing list",
        "buttontext": "Go to confirm",
    })


@group_required('type3staff')
def confirm_mailing(request):
    if request.method == 'POST':
        mailing_obj = get_object_or_404(Mailing, id=request.POST.get('mailingid', None))
        form = ConfirmForm(request.POST)
        if form.is_valid():
            # loop over all collected email addresses to create a message
            mails = []
            for recipient in mailing_obj.RecipientsStaff.all() | mailing_obj.RecipientsStudents.all():
                mails.append({
                    'template': 'email/supportstaff_email.html',
                    'email': recipient.email,
                    'subject': mailing_obj.Subject,
                    'context': {
                        'message': mailing_obj.Message,
                        'name': recipient.usermeta.get_nice_name(),
                    }
                })
            EmailThreadTemplate(mails).start()
            mailing_obj.Sent = True
            mailing_obj.save()
            return render(request, "support/email_progress.html")
        raise PermissionDenied('The confirm checkbox was unchecked.')
    raise PermissionDenied("No post data supplied!")


@group_required('studyadvisors', 'directors')
def add_promotion(request):
    """
    Make a new promotions item in the sidebar

    :param request:
    :return:
    """
    user = request.user
    if request.method == 'POST':
        form = PromotionForm(request.POST, request.FILES, request=request)
        if form.is_valid():
            form.save(commit=True)
            return render(request, "base.html",
                          {"Message": "Promotion saved!", "return": "support:editpromotions"})
    else:
        form = PromotionForm(request=request)
    return render(request, 'GenericForm.html',
                  {'form': form, 'formtitle': 'Make a new promotion', 'buttontext': 'Save'})


@group_required('studyadvisors', 'directors')
def edit_promotion(request):
    """
    Edit promotions.
    These files are shown on the sidebar for every logged in user.

    :param request:
    """
    formSet = modelformset_factory(Promotion, form=PromotionForm, can_delete=True, extra=0)
    qu = Promotion.objects.all()
    formset = formSet(queryset=qu)

    if request.method == 'POST':
        formset = formSet(request.POST, request.FILES)
        if formset.is_valid():
            formset.save()
            return render(request, "base.html",
                          {"Message": "Promotions changes saved!", "return": "support:editpromotions"})
    return render(request, 'GenericForm.html',
                  {'formset': formset, 'formtitle': 'All sidebar promotions', 'buttontext': 'Save changes'})


@group_required('studyadvisors', 'directors')
def edit_menu_links(request):
    """
    Edit links in the menu to external resources
    :param request:
    :return:
    """
    formSet = modelformset_factory(MenuLink, form=MenuLinkForm, can_delete=True, extra=1)
    qu = MenuLink.objects.all()
    formset = formSet(queryset=qu)
    if request.method == 'POST':
        formset = formSet(request.POST, request.FILES)
        if formset.is_valid():
            formset.save()
            return render(request, "base.html",
                          {
                              "Message": "Study guide menu link changes saved! <br />Note that it can take some time for the buttons to appear, as the menu is cached.",
                              "return": "support:editmenulinks"})
    return render(request, 'GenericForm.html',
                  {'formset': formset, 'formtitle': 'All Study Guide Menu links', 'buttontext': 'Save changes'})


@group_required('studyadvisors', 'directors')
def groupadministrators_form(request):
    if request.method == 'POST':
        form = GroupadministratorEdit(request.POST)
        if form.is_valid():
            administratorusergroup = Group.objects.get(name='groupadministrator')
            group = form.cleaned_data['group']
            for u in form.cleaned_data['readmembers']:
                g, created = GroupAdministratorThrough.objects.get_or_create(Group=group, User=u)
                g.Super = False
                g.save()
                u.groups.add(administratorusergroup)
                u.save()
            for u in form.cleaned_data['writemembers']:
                g, created = GroupAdministratorThrough.objects.get_or_create(Group=group, User=u)
                g.Super = True
                g.save()
                u.groups.add(administratorusergroup)
                u.save()
            for g in GroupAdministratorThrough.objects.filter(Group=group):
                if g.User not in form.cleaned_data['readmembers'] and g.User not in form.cleaned_data['writemembers']:
                    delete_object(g)
                    if g.User.administratoredgroups.count() == 0:
                        g.User.groups.remove(administratorusergroup)
                        g.User.save()
            return render(request, 'base.html', {
                'Message': 'Administrators saved!',
                'return': 'support:groupadministratorsform',
            })
    else:
        form = GroupadministratorEdit()

    return render(request, 'support/groupadministrators.html', {
        'form': form,
        'formtitle': 'Set Group Administrators',
        'buttontext': 'save',
    })


#######
# Lists#
#######
@group_required('studyadvisors', 'directors')
def list_users(request):
    """
    List of all active users, including upgrade/downgrade button for staff and impersonate button for admins

    :param request:
    :return:
    """
    return render(request, "support/list_users.html", {
        "users": User.objects.all().select_related('allowedaccess').prefetch_related('groups', 'usermeta', 'registration', 'administratoredgroups'),
        'hide_sidebar': True,
    })
    # if request.user.is_superuser:
    #     key = 'listusersbodyhtmladmin'
    # else:
    #     key = 'listusersbodyhtml'
    # bodyhtml = cache.get(key)
    # if bodyhtml is None:
    #     bodyhtml = render_block_to_string('support/list_users.html', 'body', {
    #         "users": User.objects.all().prefetch_related('groups', 'usermeta', 'registration'),
    #         "user": request.user})
    #     cache.set(key, bodyhtml, 15 * 60)
    #
    # return render(request, "support/list_users.html", {
    #     "bodyhtml": bodyhtml,
    # })


@group_required('studyadvisors', 'directors')
def user_info(request, pk):
    """
    Return information and privacy data of given user.

    :param request:
    :param pk:
    :return:
    """

    def json_serial(obj):
        """JSON serializer for objects not serializable by default json code"""
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()

        if isinstance(obj, User):
            return obj.__str__()
        raise TypeError("Type %s not serializable" % type(obj))

    user = get_object_or_404(User, pk=pk)
    user_model = [[field.name, getattr(user, field.name)] for field in user._meta.fields if
                  field.name.lower() not in ['password', 'pass', 'key', 'secret', 'token', 'signature']]
    try:
        usermeta_model = [[field.name, getattr(user.usermeta, field.name)] for field in user.usermeta._meta.fields]
    except UserMeta.DoesNotExist:
        usermeta_model = []
    related = []
    for obj in user._meta.related_objects + user._meta.many_to_many:
        if hasattr(user, obj.name):
            try:
                related.append([obj.name, [obj2.__str__() for obj2 in getattr(user, obj.name).all()]])
            except:
                related.append([obj.name, [getattr(user, obj.name).__str__()]])
        else:
            related.append([obj.name, []])
    # distribution = []
    # if user.groups.exists():
    #     ds = []
    #     for p in user.projects.all():
    #         ds += list(p.distributions.all())
    #     for p in user.projectsresponsible.all():
    #         ds += list(p.distributions.all())
    #     print(ds)
    # else:  # student
    #     ds = user.distributions.all()
    # for d in ds:
    #     for obj in d._meta.related_objects + d._meta.many_to_many:
    #         if hasattr(d, obj.name):
    #             try:
    #                 distribution.append([obj.name, [obj2.__str__() for obj2 in getattr(d, obj.name).all()]])
    #             except:
    #                 distribution.append([obj.name, [getattr(d, obj.name).__str__()]])
    #         else:
    #             distribution.append([obj.name, []])
    return render(request, 'index/user_info.html', {
        'view_user': user,
        'user_model': user_model,
        'usermeta_model': usermeta_model,
        'related': related,
        # 'distribution': distribution,
        'json': json.dumps(
            {
                'user_model': user_model,
                'usermeta_model': usermeta_model,
                'related': related,
                # 'distribution': distribution
            }, default=json_serial),
    })


@group_required('directors', 'studyadvisors')
def list_staff(request):
    """
    List all staff with a distributed projects

    :param request:
    :return:
    """

    def nint(nr):
        """
        :param <int> nr:
        :return:
        """
        if nr is None:
            return 0
        else:
            return int(nr)

    staff = get_all_staff().filter(
        Q(groups=get_grouptype("assistants")) | Q(groups=get_grouptype("supervisors"))).prefetch_related(
        'projectsresponsible', 'projects')
    se = []
    for s in staff:
        pt1 = s.projectsresponsible.count()
        pt2 = s.projects.count()
        pts = pt1 + pt2
        dt1 = nint(s.projectsresponsible.all().annotate(Count('distributions')).aggregate(Sum('distributions__count'))[
                       'distributions__count__sum'])
        dt2 = nint(s.projects.all().annotate(Count('distributions')).aggregate(Sum('distributions__count'))[
                       'distributions__count__sum'])
        dts = dt1 + dt2
        se.append({"user": s, "pt1": pt1, "pt2": pt2, "pts": pts, "dt1": dt1, "dt2": dt2, "dts": dts})
    return render(request, 'support/list_staff.html', {"staff": se})


@group_required('studyadvisors', 'directors')
def list_staff_projects(request, pk):
    """
    List all projects of a staff member
    """
    user = get_all_staff().get(id=pk)

    projects = user.projectsresponsible.all() | user.projects.all()
    projects = projects.select_related('ResponsibleStaff', 'Group'). \
        prefetch_related('Assistants', 'Program', 'distributions', 'applications')

    return render(request, 'projects/list_projects_custom.html',
                  {"title": "Proposals from " + user.usermeta.get_nice_name(), "projects": projects})


@group_required('supervisors', 'assistants', 'directors', 'studyadvisors', 'groupadministrator')
def list_students(request):
    """
    For support staff, responsibles and assistants to view their students.
    List all students with distributions that the current user is allowed to see.

    :param request:
    :return:
    """
    des = get_distributions(request.user).select_related('Project__ResponsibleStaff', 'Project__Group',
                                                         'Student__usermeta', 'Student__registration'). \
        prefetch_related('Project__Assistants', 'Project__Program')
    return render(request, "support/list_distributions.html", {'des': des,
                                                               'hide_sidebar': True})


@group_required('studyadvisors', 'directors')
def edit_user_groups(request, pk):
    """
    Change the groups of a given user.

    :param request:
    :param pk: user id
    :return:
    """
    usr = get_object_or_404(User, pk=pk)
    if not usr.groups.exists():
        if not usr.is_superuser:
            raise PermissionDenied("This user is a student. Students cannot have groups.")
    if get_grouptype("unverified") in usr.groups.all():
        raise PermissionDenied("This user is not yet verified. Please verify first in the user list.")

    if request.method == "POST":
        form = UserGroupsForm(request.POST, instance=usr)
        if form.is_valid():
            if form.has_changed():
                # call print list here to force query execute
                old = print_list(usr.groups.all().values_list('name', flat=True))
                form.save()
                new = print_list(usr.groups.all().values_list('name', flat=True))
                send_mail("user groups changed", "email/user_groups_changed.html",
                          {'oldgroups': old,
                           'newgroups': new,
                           'user': usr},
                          usr.email)
                return render(request, 'base.html', {
                    'Message': 'User groups saved!',
                    'return': 'support:listusers',
                })
            return render(request, 'base.html', {
                'Message': 'No changes made.',
                'return': 'support:listusers',
            })
    else:
        form = UserGroupsForm(instance=usr)
    return render(request, 'support/user_groups_form.html', {
        'formtitle': 'Set user groups for {}'.format(usr.username),
        'form': form,
    })


@group_required('studyadvisors', 'directors')
def toggle_disable_user(request, pk):
    """
    en/disable a user to prevent him/her from login

    :param request:
    :param pk:
    :return:
    """
    usr = get_object_or_404(User, pk=pk)
    usr.is_active = not usr.is_active
    usr.save()
    return redirect('support:listusers')

#
# @group_required('type4staff')
# def list_group_projects(request):
#     """
#     List all projects of a group.
#
#     :param request:
#     :return:
#     """
#     obj = get_object_or_404(CapacityGroupAdministration, Members__id=request.user.id)
#     props = get_all_projects(old=True).filter(Group=obj.Group)
#     return render(request, "projects/ProposalsCustomList.html", {
#         "projects": props,
#         "title": "Proposals of My Group"
#     })

# not used
# @group_required('studyadvisors')
# def list_studyadvisor_projects(request):
#     """
#     List all projects for the studyadvisor, so includes old and private ones
#
#     :param request:
#     :return:
#     """
#     return render(request, "projects/ProposalsCustomList.html", {
#         "projects": get_all_projects(old=True),
#         "title": "All projects in system"
#     })


#######
# Cache#
#######
#
# @group_required('studyadvisors', 'directors')
# def list_users_clear_cache(request):
#     """
#     Clear cache for list users
#
#     :param request:
#     :return:
#     """
#     cache.delete('listusersbodyhtmladmin')
#     cache.delete('listusersbodyhtml')
#
#     return render(request, 'base.html', {'Message': 'Cache cleared for users list', "return": "support:listusers"})

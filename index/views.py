from os import path

from django.conf import settings
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.files.base import ContentFile
from django.core.files.images import get_image_dimensions
from django.core.files.storage import default_storage
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.http.response import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone, formats

from general_form import ConfirmForm
from general_mail import send_mail
from general_model import get_ext, filename_default
from general_model import print_list
from index.decorators import superuser_required, group_required
from projects.utils import get_visible_projects
from .forms import FeedbackForm, SettingsForm, CloseFeedbackReportForm
from .models import FeedbackReport, UserMeta, UserAcceptedTerms, Term


# @cache_for_anonymous
def index(request):
    """
    The index page, home page, for all users. This displays a simple help string based on the timephase and an
    extensive help text (supplied in the template).

    :param request:
    :return: render of the index page.
    """
    if request.user.is_authenticated:
        date_projects = []
        dates = []
        days = []
        try:
            last_login = request.user.logins.all().order_by('-Timestamp')[1].Timestamp
            changed_projects = get_visible_projects(request.user).filter(TimeStamp__gte=last_login).distinct().order_by(
                '-TimeStamp')
            for x in changed_projects.values_list('TimeStamp', flat=True):  # buckets of days.
                if x.day not in days:  # make days unique.
                    dates.append('On ' + formats.date_format(x, format='DATE_FORMAT'))
                    days.append(x.day)
            for day, date in zip(days, dates):  # fill day-buckets with projects.
                date_projects.append([date, changed_projects.filter(TimeStamp__day=day)])
        except IndexError:  # on first login of user, don't show changed projects.
            pass
        return render(request, "index/index.html", context={
            'support_name': settings.SUPPORT_NAME,
            'support_role': settings.SUPPORT_ROLE,
            'support_email': settings.SUPPORT_EMAIL,
            'date_projects': date_projects,
        })
    else:
        # anonymous users index view.
        return render(request, "index/index.html", context={
            'support_name': settings.SUPPORT_NAME,
            'support_role': settings.SUPPORT_ROLE,
        })


def logout(request):
    """
    User logout. This function is still used, also for SAML

    :param request:
    :return:
    """
    if not request.user.is_authenticated:
        return HttpResponseRedirect('/')
    auth_logout(request)
    return render(request, "base.html", {"Message": "You are now logged out. "
                                                    "<a href='/' title='Home'>Go back to the homepage</a>.<br />"
                                                    "To logout of the TU/e single sign on please close your browser."})


@superuser_required()
def list_feedback(request):
    """
    List the feedback supplied via the feedback button. Only for superusers.

    :param request:
    :return:
    """
    return render(request, "index/list_feedback.html", {
        'feedback_list': FeedbackReport.objects.filter(~Q(Status=3))
    })


@login_required
def feedback_form(request):
    """
    The form to give feedback using the feedback button. All users can supply feedback. Superusers can view it.

    :param request:
    :return:
    """
    if request.method != "POST":
        return render(request, "base.html", {
            "Message": "Please do not access this page directly."
        })

    form = FeedbackForm(initial={
        'Url': request.POST['id_Url'],
    })

    return render(request, "index/feedback_form.html", {
        "form": form,
        "formtitle": "Feedback Form",
        "buttontext": "Send",
        'support_name': settings.SUPPORT_NAME,
        "actionlink": "index:feedback_submit"  # redirect to feedback_submit
    })


@login_required
def feedback_submit(request):
    """
    The 'thanks' page after feedback is submitted by a user.
    Also shows form validation errors if present.

    :param request:
    :return:
    """
    if request.method != "POST":
        return render(request, "base.html", {
            "Message": "Please do not access this page directly."
        })
    form = FeedbackForm(request.POST)
    if form.is_valid():
        feedback = form.save(commit=False)
        feedback.Reporter = request.user
        feedback.Status = 1
        feedback.save()
        send_mail("feedback report created", "email/feedback_report_email_created.html", {
            "report": feedback
        }, feedback.Reporter.email)
        send_mail("feedback report created", "email/feedback_report_admin.html", {
            "report": feedback
        }, settings.CONTACT_EMAIL)
        return render(request, "base.html", {
            "Message": "Feedback saved, thank you for taking the time to improve the system!"
        })
    return render(request, "index/feedback_form.html", {
        "form": form,
        "formtitle": "Feedback Form",
        "buttontext": "Send",
        "support_name": settings.SUPPORT_NAME,
    })


@superuser_required()
def feedback_confirm(request, pk):
    """
    Form to confirm the feedback given by a user. Only for superusers. Sends a simple confirm mail to the user.

    :param request:
    :param pk: id of the feedback report
    :return:
    """

    obj = get_object_or_404(FeedbackReport, pk=pk)
    if obj.Status != 1:
        return render(request, "base.html", {
            "Message": "Report is not in open status.",
            "return": "index:list_feedback"
        })
    obj.Status = 2
    obj.save()
    send_mail("feedback report", "email/feedback_report_email_statuschange.html", {
        "report": obj
    }, obj.Reporter.email)

    return render(request, "base.html", {
        "Message": "Report confirmed and reporter notified.",
        "return": "index:list_feedback"
    })


@superuser_required()
def feedback_close(request, pk):
    """
    Close a feedback report. Send a custom message to the user that gave the feedback. Only for superusers

    :param request:
    :param pk: id of the feedback report
    :return:
    """
    obj = get_object_or_404(FeedbackReport, pk=pk)

    if obj.Status == 3:
        return render(request, "base.html", {
            "Message": "Report is already closed.",
            "return": "index:list_feedback"
        })

    if request.method == "POST":
        form = CloseFeedbackReportForm(request.POST, initial={
            'email': obj.Reporter.email
        })
        if form.is_valid():
            obj.Status = 3
            obj.save()
            send_mail("feedback report", "email/feedback_report_email_statuschange.html", {
                "report": obj,
                "message": form.cleaned_data["message"],
            }, obj.Reporter.email)

            return render(request, "base.html", {
                "Message": "Report closed and reporter notified.",
                "return": "index:list_feedback"
            })
    else:
        form = CloseFeedbackReportForm(initial={
            'email': obj.Reporter.email
        })

    return render(request, "GenericForm.html", {
        "formtitle": "Close Feedback Report",
        "buttontext": "Close",
        "form": form
    })


@login_required
def profile(request):
    """
    Displays a profile page for the user.
    For staff members displays the groups that user is in
    For students displays LDAP data and course enrollments (via studyweb).

    :param request:
    :return:
    """
    try:
        meta = request.user.usermeta
    except UserMeta.DoesNotExist:
        meta = UserMeta()
        request.user.usermeta = meta
        meta.save()
        request.user.save()

    groups = request.user.groups
    if groups.exists() or request.user.is_superuser:
        vars = {
            "student": False,
            "meta": meta,
            "SuppressStatusMails": meta.SuppressStatusMails,
            "supervisor": groups.filter(name='supervisors'),
            "assistant": groups.filter(name='assistants'),
            # "external": groups.filter(name='external'),
            "studyadvisor": groups.filter(name='studyadvisors'),
        }
    else:
        vars = {
            "student": True,
            "meta": meta,
            "SuppressStatusMails": meta.SuppressStatusMails,
        }
    return render(request, "index/profile.html", vars)


@login_required
def user_settings(request):
    """
    Let a user change its settings, like email preferences.

    :param request:
    :return:
    """
    try:
        meta = request.user.usermeta
    except UserMeta.DoesNotExist:
        meta = UserMeta()
        request.user.usermeta = meta
        meta.save()
        request.user.save()

    if request.method == 'POST':
        form = SettingsForm(request.POST, instance=meta)
        if form.is_valid():
            form.save()
            return render(request, "base.html", {
                "Message": 'Settings saved!',
                'return': 'index:profile',
            })
    else:
        form = SettingsForm(instance=meta)

    return render(request, "GenericForm.html", {
        "form": form,
        "formtitle": "Change user settings",
        "buttontext": "Save"
    })


@login_required
def terms_form(request):
    """
    Form for a user to accept the terms of use.

    :param request:
    :return:
    """
    try:
        # already accepted, redirect user to login
        obj = request.user.termsaccepted
        if obj.Stamp <= timezone.now():
            return HttpResponseRedirect('/')
    except UserAcceptedTerms.DoesNotExist:
        pass

    if request.method == 'POST':
        form = ConfirmForm(request.POST)
        if form.is_valid():
            # user accepted terms. Possible already accepted terms in a parallel session, so get_or_create.
            UserAcceptedTerms.objects.get_or_create(User=request.user)
            return HttpResponseRedirect('/')
    else:
        form = ConfirmForm()

    return render(request, 'index/terms.html', {
        'form': form,
        'formtitle': 'I have read and accepted the Terms of Services',
        'buttontext': 'Confirm',
        'terms': Term.objects.all()
    })


@group_required('studyadvisors', 'directors')
def markdown_upload(request):
    """
    Upload an image to the server and store it to the folder defined in
    Note that the image folder must be created first and with write access.
    :return: The relative path of the uploaded file, or an error among with the
    corresponding HTTP error code.
    """
    # required image dimensions for markdown
    minw = 40
    minh = 40
    maxw = 1600
    maxh = 1200
    # only uploads from these forms are allowed:
    markdown_upload_whitelist = ['studyguide/masterprogram/edit/', 'studyguide/capacitygroup/edit/', 'studyguide/masterprogram/add/', 'studyguide/capacitygroup/add/']
    if "HTTP_REFERER" in request.META:
        if all([markdown_upload_whitelist_item not in request.META['HTTP_REFERER'] for markdown_upload_whitelist_item in markdown_upload_whitelist]):
            return JsonResponse({'error': 'Image upload is not allowed.'})
    else:
        raise PermissionDenied('Not allowed.')
    # require image
    if 'image' not in request.FILES:
        return JsonResponse({'error': 'noFileGiven'})
    file = request.FILES['image']
    if not file.name:
        return JsonResponse({'error': 'noFileGiven'})
    if file and '.' in file.name \
            and get_ext(file.name) in settings.MARKDOWN_ALLOWED_IMAGES_TYPES:
        s = file.size
        if s > settings.MAX_UPLOAD_SIZE:
            return JsonResponse({'error': "The file is too large, it has to be at most " + str(
                round(settings.MAX_UPLOAD_SIZE / 1024 / 1024)) + "MB and is " + str(
                round(s / 1024 / 1024)) + "MB."})
        w, h = get_image_dimensions(file)
        if w < minw or h < minh:
            return JsonResponse({'error': "The image is too small, it has to be at least " + str(minw) + "px by " + str(
                minh) + "px and is only " + str(
                w) + "px by " + str(
                h) + "px."})
        if w > maxw or h > maxh:
            return JsonResponse({'error': "The image is too large, it has to be at most " + str(maxw) + "px by " + str(
                maxh) + "px and is " + str(
                w) + "px by " + str(
                h) + "px."})
        file_name = filename_default(file.name)
        file_path = path.join(settings.MEDIA_ROOT, settings.MARKDOWN_IMAGE_UPLOAD_FOLDER, file_name)
        default_storage.save(file_path, ContentFile(file.read()))
        download_path = '{}{}/{}'.format(settings.MEDIA_URL[1:], settings.MARKDOWN_IMAGE_UPLOAD_FOLDER, file_name)
        return JsonResponse({'data': {'filePath': download_path}})

    return JsonResponse({
        'error': 'This file type is not allowed. Allowed types: {}'.format(print_list(settings.MARKDOWN_ALLOWED_IMAGES_TYPES))
    }
    )


def error400(request, exception):
    """
    http 400 page, for instance wrong hostname

    :param request:
    :param exception: needed param by django.
    :return:
    """
    return render(request, "400.html", status=400)


def error403(request, exception):
    """
    http 403 page

    :param request:
    :param exception: Reason why this page is forbidden.
    :return:
    """
    return render(request, "403.html", status=403, context={"exception": exception})


def error404(request, exception):
    """
    http 404 page

    :param request:
    :param exception: needed param by django.
    :return:
    """
    return render(request, "base.html", status=404, context={
        "Message": "The page you are looking for does not exist. Please have a look at the <a href=\"/\">homepage</a>"
    })


def error500(request):
    """
    http 500 page

    :param request:
    :return:
    """
    return render(request, "50x.html", status=500, context={
        "reason": "Something went wrong in the server. "
                  "The Master Marketplace team has been automatically notified. </br>"
                  "Please help them by sending an email to "
                  "<a href=\"mailto:mastermarketplace@tue.nl?subject=BugReport\">mastermarketplace@tue.nl</a> "
                  "with more information what you were trying to do. <br/>"
                  "Thanks in advance!"
    })


def about(request):
    """
    About page

    :param request:
    :return:
    """
    return render(request, "index/about.html")

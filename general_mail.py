"""
General functions, used for mailing
"""
import json
import threading
from math import floor
from smtplib import SMTPException
from time import sleep

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template import loader
from django.utils.html import strip_tags

from index.models import UserMeta
from templates import context_processors


def send_mail(subject, email_template_name, context, to_email):
    """
    Sends a django.core.mail.EmailMultiAlternatives to `to_email`.
    """
    # append context processors, some variables from settings
    context = {**context, **context_processors.general()}
    # prepend the marketplace name to the settings
    subject = '{} {}'.format(settings.NAME_PRETTY, subject.strip())
    # generate html email
    html_email = loader.render_to_string(email_template_name, context)
    # attach text and html message
    email_message = EmailMultiAlternatives(subject, strip_tags(html_email), settings.FROM_EMAIL_ADDRESS, [to_email])
    email_message.attach_alternative(html_email, 'text/html')
    # send
    try:
        email_message.send()
    except SMTPException:
        with open("mailcrash.log", "a") as stream:
            stream.write("Mail to {} could not be send:\n{}\n".format(to_email, html_email))
    except ConnectionRefusedError:
        if settings.DEBUG:
            print("Send mail refused!")
        else:
            with open("mailcrash.log", "a") as stream:
                stream.write("Mail to {} could not be send:\n{}\n".format(to_email, html_email))


def mail_project_all(request, project, message=''):
    """
    General function to mail a 'message' to all users responsible or assistant to a given proposal.
    Except the user making the request (-> new behavior 2018).

    :param request: the request of user making the change. This user wil be excluded from mails
    :param project: The proposal that is changed
    :param message: Message string
    :return:
    """
    emails = []
    if project.Status != 2:
        for assistant in project.Assistants.all():
            if (not is_mail_suppressed(assistant)) and request.user != assistant:
                emails.append(assistant.email)
    # for external in project.ExternalStaff.all():
    #     if not is_mail_suppressed(external):
    #         emails.append(external.email)
    if project.Status != 1:
        if (not is_mail_suppressed(project.ResponsibleStaff)) and request.user != project.ResponsibleStaff:
            emails.append(project.ResponsibleStaff.email)

    context = {
        'project': project,
        'message': message
    }
    for email in emails:
        send_mail("project updated", "email/project_updated_email.html", context, email)


def mail_project_single(project, staff, message=''):
    """
    mail a staff member with a given message about a project.

    :param project: The project to mail about
    :param staff: The staff that gets the mail for this project
    :param message: message string
    :return:
    """
    email = staff.email
    context = {
        'project': project,
        'message': message,
    }
    send_mail('project changed', "email/project_staff_changed_email.html", context, email)


def is_mail_suppressed(user):
    """
    Check if a user has the 'SuppressStatusMails' setting set to True. This is if a user doesn't want to receive mails.

    :param user:
    :return:
    """
    try:
        meta = user.usermeta
    except UserMeta.DoesNotExist:
        meta = UserMeta()
        user.usermeta = meta
        meta.save()
        user.save()
    return meta.SuppressStatusMails


class EmailThreadTemplate(threading.Thread):
    """
    Same as email thread but with a template.
    input is array of mails with subject, template and destination
    """

    def __init__(self, mails):
        self.mails = mails
        super().__init__()
        self.channel_layer = get_channel_layer()

    def run(self):
        sleep(1)
        for i, mail in enumerate(self.mails):
            if not mail:
                continue
            if not settings.TESTING:
                async_to_sync(self.channel_layer.group_send)('email_progress',
                                                             {'type': 'update', 'text': json.dumps({
                                                                 'email': mail['email'],
                                                                 'progress': floor(((i + 1) / len(self.mails)) * 100),
                                                             })})
            send_mail(mail['subject'], mail['template'], mail['context'], mail['email'])

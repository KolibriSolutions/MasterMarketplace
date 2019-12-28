import json
from datetime import datetime

from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404

from index.decorators import group_required, superuser_required
from general_view import get_sessions
from .models import UserLogin, RegistrationTracking, ApplicationTracking, DistributionTracking, ProjectStatusChange


# TODO: add tracking for granting and revoking access


@superuser_required()
def list_user_login(request):
    """
    Shows the list of loginattempts by time.

    :param request:
    :return:
    """
    return render(request, "tracking/listUserLog.html", {
        "userlogs": list(UserLogin.objects.order_by('-Timestamp')),
    })


@superuser_required()
def list_project_status_change(request):
    """
    List of proposal status changes.

    :param request:
    :return:
    """
    return render(request, "tracking/listTrackingStatus.html", {
        "trackings": ProjectStatusChange.objects.all()
    })


@superuser_required()
def list_application_change(request):
    """
    List of application-apply and application-retracts of all students.

    :param request:
    :return:
    """
    return render(request, "tracking/listTrackingApplication.html", {
        'trackinglist': ApplicationTracking.objects.order_by('-Timestamp')
    })


@superuser_required()
def list_distribution_change(request):
    """
    List of distributes and undistributes of all students.

    :param request:
    :return:
    """
    return render(request, "tracking/listTrackingDistribution.html", {
        'trackinglist': DistributionTracking.objects.order_by('-Timestamp')
    })


@group_required('studyadvisors', 'directors')
def list_registration_changes(request):
    return render(request, 'tracking/listRegistrationChange.html', {
        'changes': RegistrationTracking.objects.all()
    })


@superuser_required()
def telemetry_user_detail(request, pk):
    user = get_object_or_404(User, pk=pk)

    try:
        with open('tracking/telemetry/data/{}.log'.format(user.username), 'r') as stream:
            telemetry = json.loads('[{}]'.format(','.join(stream.readlines())).replace('\n', ''))
    except:
        telemetry = []

    pages_count = {}

    for line in telemetry:
        line['timestamp'] = datetime.fromtimestamp(line['timestamp'])
        try:
            pages_count[line['path']] += 1
        except:
            pages_count[line['path']] = 1

    return render(request, 'tracking/userTrackingDetail.html', {
        'session': len(get_sessions(user)) != 0,
        'target': user,
        'telemetry': telemetry,
        'toppages': sorted(pages_count, key=pages_count.__getitem__, reverse=True)[:3],
    })

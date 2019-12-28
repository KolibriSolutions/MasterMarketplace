import json

from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from registration.decorators import api_protected
from registration.models import PlannedCourse, Registration, Planning
from registration.utils import get_planning_json


@csrf_exempt
@api_protected
@require_http_methods(['POST'])
def add_year(request, user):
    """
    Add a year to the planning

    :param request:
    :param user:
    :return:
    """
    try:
        reg = user.registration
        planning = reg.courseplanning
    except (Registration.DoesNotExist, Planning.DoesNotExist):
        return HttpResponseBadRequest('user has no program registration yet')

    if planning.Years == 9:
        return JsonResponse({'type': 'warning', "message": "9 years is the maximum. Please don't study that long..."})
    planning.Years += 1
    planning.save()
    return JsonResponse({'type': 'success', "message": '{} years planned.'.format(planning.Years)})


@csrf_exempt
@api_protected
@require_http_methods(['POST'])
def remove_year(request, user):
    """
    Remove a year from the planning.

    :param request:
    :param user:
    :return:
    """
    try:
        reg = user.registration
        planning = reg.courseplanning
    except (Registration.DoesNotExist, Planning.DoesNotExist):
        return HttpResponseBadRequest('user has no program registration yet')

    if planning.Years > 2:
        # remove all planned courses in that year
        PlannedCourse.objects.filter(Planning=planning, Year=planning.Years).delete()
        planning.Years -= 1
        planning.save()
    else:
        return JsonResponse({'type': 'warning', "message": "2 years is the minimum."})
    return JsonResponse({'type': 'success', "message": '{} years planned.'.format(planning.Years)})


# order matters: csrf_exempt needs to be last otherwise the api_protected does not work correctly
@csrf_exempt
@api_protected
@require_http_methods(['POST'])
def save_planning(request, user):
    """
    Save planning from courseplanner

    :param request:
    :param user:
    :return: JSON
    """
    data = request.POST.get('planning', None)
    if data is None:
        return HttpResponseBadRequest('Planning not found')
    try:
        data = json.loads(data)
    except:
        return HttpResponseBadRequest('Invalid json data')

    if len(data.keys()) != user.registration.courseplanning.Years * 4:
        return HttpResponseBadRequest('Invalid json data')

    try:
        reg = user.registration
    except Registration.DoesNotExist:
        return HttpResponseBadRequest('Please register yourself first using the Registration menu.')

    # clear the whole planning and rebuild it from the json that is send
    # keep the queryset in memory to reapply to db in case of errors
    oldcourses = reg.courseplanning.courses.all()
    oldcourses_codes = reg.courseplanning.get_course_codes()
    oldcourses.delete()

    try:
        for quartile, courses in data.items():
            year = int(quartile[1])
            qnum = int(quartile[3])
            for c in courses:
                if PlannedCourse.objects.filter(Code=c, Planning=reg.courseplanning).exists():
                    # only allow each course to be planned once.
                    return JsonResponse({'type': 'warning', 'message': 'Course {} is planned twice. Please remove one instance.'.format(c)})
                else:
                    p = PlannedCourse(Code=c, Year=year, Quartile=qnum, Planning=reg.courseplanning)
                    p.save()
    except:
        # delete all changes made and resave the old objects
        reg.courseplanning.courses.all().delete()
        oldcourses.save()
        return JsonResponse({"type": "warning", 'message': 'Data invalid. Old planning is restored.'})

    # check if there are courses swapped out, then change state of registration
    # function returns set so can use equality check
    if oldcourses_codes != reg.courseplanning.get_course_codes():
        reg.State = 1
        reg.save()

    return JsonResponse({"type": "success", 'message': 'Data saved!'})


@csrf_exempt
@api_protected
@require_http_methods(['POST'])
def get_planning(request, user):
    try:
        reg = user.registration
        planning = reg.courseplanning
    except (Registration.DoesNotExist, Planning.DoesNotExist):
        return HttpResponseBadRequest('user has no program registration yet')
    planning = get_planning_json(planning)

    return JsonResponse(planning)

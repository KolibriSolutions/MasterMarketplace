from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.cache import cache
from django.conf import settings
from tracking.models import ProjectTracking


def get_ProjectTracking(proposal):
    """
    try retrieving the object from cache, if not in cache from db, if not in db, create it. update cache accordingly

    :param proposal:
    :return:
    """
    c_track = cache.get('trackprop{}'.format(proposal.id))
    if c_track is None:
        try:
            track = ProjectTracking.objects.get(Subject=proposal)
        except ProjectTracking.DoesNotExist:
            track = ProjectTracking()
            track.Subject = proposal
            track.save()
        cache.set('trackprop{}'.format(proposal.id), track, None)
        return track
    else:
        return c_track


def tracking_visit_project(project, user):
    """
    Add a proposal-visit to the list of visitors to count unique student views to a proposal

    :param project: the proposal
    :param user: the visiting user.
    :return:
    """
    # only for students
    if user.groups.exists() or user.is_superuser:
        return

    # only for published, status=3 for master, status=4 for bep.
    if project.Status != 3:
        return

    # retrieve object
    track = get_ProjectTracking(project)

    # add if it is unique visitor and write to both db and cache
    if user not in track.UniqueVisitors.all():
        track.UniqueVisitors.add(user)
        track.save()
        cache.set('trackprop{}'.format(project.id), track, None)

        # notify listeners
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)('viewnumber{}'.format(project.id), {
            'type': 'update',
            'text': str(track.UniqueVisitors.count()),
        })

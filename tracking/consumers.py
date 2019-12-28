from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib import auth
from django.contrib.auth.models import Group
from django.shortcuts import get_object_or_404

from projects.models import Project
from .utils import get_ProjectTracking


def checkauthcurrentviewnumber(user, track):
    if user != track.Subject.ResponsibleStaff and \
            user not in track.Subject.Assistants.all() and \
            auth.models.Group.objects.get(name="studyadvisors") not in user.groups.all() and \
            not user.is_superuser:
        return True
    return False


class CurrentViewNumberConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.pk = self.scope['url_route']['kwargs']['pk']
        self.project = await database_sync_to_async(get_object_or_404)(Project, pk=self.pk)
        self.track = await database_sync_to_async(get_ProjectTracking)(self.project)
        self.user = self.scope['user']
        if self.track.Subject.Status != 3:
            await self.close()
            return
        if await database_sync_to_async(checkauthcurrentviewnumber)(self.user, self.track):
            await self.close()
            return

        await self.channel_layer.group_add(
            'viewnumber{}'.format(self.pk),
            self.channel_name
        )
        await self.accept()
        await self.send(text_data=str(await database_sync_to_async(self.track.UniqueVisitors.count)()))

    async def disconnect(self, code):
        await self.channel_layer.group_discard(
            'viewnumber{}'.format(self.pk),
            self.channel_name
        )

    async def receive(self, text_data):
        pass

    async def update(self, event):
        # Handles the messages on channel
        await self.send(text_data=event["text"])

import logging

from channels.db import database_sync_to_async
from channels.exceptions import StopConsumer
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.conf import settings
from rest_framework import exceptions, status

from django_tasks.serializers import DocTaskSerializer, TaskRequestSerializer
from django_tasks.doctask_scheduler import DocTaskScheduler, schedule_tasks
from django_tasks.task_cache import TaskCache
from django_tasks.websocket import close_codes


class TaskEventsConsumer(AsyncJsonWebsocketConsumer):
    @property
    def user_group(self) -> str:
        """The name of the group of consumers that is assigned to the user."""
        return f"{self.scope['user'].username}_{settings.CHANNEL_TASKS.channel_group}"

    @property
    def request_id(self) -> str:
        """The request ID provided in the corresponding header, if any."""
        for name, value in self.scope.get('headers', []):
            if name == b'request-id':
                return value.decode()
        return ''

    async def task_started(self, event):
        """Echoes the task.started document."""
        await self.send_json(content=event)

    async def task_success(self, event):
        """Echoes the task.success document."""
        await self.send_json(content=event)

    async def task_cancelled(self, event):
        """Echoes the task.cancelled document."""
        await self.send_json(content=event)

    async def task_error(self, event):
        """Echoes the task.error document."""
        await self.send_json(content=event)

    async def task_badrequest(self, event):
        """Echoes the task.badrequest document."""
        await self.send_json(content=event)

    async def group_send(self, event):
        """Distributes the given `event` through the group of the user of this instance."""
        await self.channel_layer.group_send(self.user_group, event)

    async def stop_unauthorized(self):
        """Stops the consumer if the user is not authenticated."""
        if not self.scope['user'].is_authenticated:
            logging.getLogger('django').warning('Unauthenticated user %s. Closing websocket.', self.scope['user'])
            await self.close(code=close_codes.UNAUTHORIZED)
            raise StopConsumer()

    async def connect(self):
        """Performs authentication and set-up actions on connection."""
        await self.stop_unauthorized()
        await super().connect()
        self.user_task_cache = TaskCache(self.scope['user'].username)
        await self.channel_layer.group_add(self.user_group, self.channel_name)
        logging.getLogger('django').debug(
            'Connected user "%s" through channel %s.', self.scope['user'].username, self.channel_name)

    async def disconnect(self, close_code):
        """Performs clean-up actions on disconnection."""
        await self.channel_layer.group_discard(self.user_group, self.channel_name)
        logging.getLogger('django').debug(
            'Disconnected channel %s. User: %s. CloseCode: %s',
            self.channel_name, self.scope['user'].username, close_code)

    async def schedule_tasks(self, request_data):
        """Processes task schedule websocket requests."""
        logging.getLogger('django').debug(
            'Processing task schedule through channel %s. Data: %s', self.channel_name, request_data)
        try:
            many_serializer = await database_sync_to_async(
                DocTaskSerializer.get_task_group_serializer)(request_data['content'])
        except exceptions.ValidationError as error:
            await self.send_bad_request_message(error)
        else:
            await schedule_tasks(self.request_id, self.scope['user'].username, *many_serializer.data)

    async def schedule_doctasks(self, request_data):
        """Processes doc-task schedule websocket requests."""
        logging.getLogger('django').debug(
            'Processing DocTask schedule through channel %s. Data: %s', self.channel_name, request_data)
        try:
            many_serializer, doctasks = await database_sync_to_async(
                DocTaskSerializer.create_doctask_group)(request_data['content'])
        except exceptions.ValidationError as error:
            await self.send_bad_request_message(error)
        else:
            await DocTaskScheduler.schedule_doctasks(
                self.request_id, self.scope['user'].username, *many_serializer.data)

    @database_sync_to_async
    def clear_task_cache(self, request_data):
        """Clears a specific task cache."""
        logging.getLogger('django').debug(
            'Processing cache clear through channel %s. Data: %s', self.channel_name, request_data)
        self.user_task_cache.clear_task_cache(request_data['content']['task_id'])

    async def receive_json(self, request_data):
        """Performs a supported action if valid data is provided, else sends a 400 message."""
        serializer = TaskRequestSerializer(data=request_data)

        try:
            serializer.is_valid(raise_exception=True)
        except exceptions.ValidationError as error:
            await self.send_bad_request_message(error)
        else:
            await getattr(self, serializer.data['action'])(serializer.data)

    async def send_bad_request_message(self, error: exceptions.ValidationError):
        """Broadcasts an HTTP 400 message through the user's group of consumers."""
        await self.group_send({
            'type': 'task.badrequest', 'content': {
                'details': error.get_full_details(),
                'request_id': self.request_id,
                'http_status': status.HTTP_400_BAD_REQUEST,
            }
        })

import asyncio
import logging
import time

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.conf import settings
from django.core.cache import cache
from rest_framework import exceptions, status

from django_tasks.serializers import DocTaskSerializer, TaskRequestSerializer
from django_tasks.doctask_scheduler import DocTaskScheduler, schedule_tasks
from django_tasks.task_inspector import get_coro_info
from django_tasks.task_runner import TaskRunner


class TaskEventsConsumer(AsyncJsonWebsocketConsumer):
    @property
    def cache_key(self):
        return f"{self.scope['user'].username}.task_events"

    @property
    def user_group(self):
        return f"{self.scope['user'].username}_{settings.CHANNEL_TASKS.channel_group}"

    async def group_send(self, event):
        await self.channel_layer.group_send(self.user_group, event)

    async def connect(self):
        await super().connect()
        await self.channel_layer.group_add(self.user_group, self.channel_name)

    async def disconnect(self, close_code):
        logging.getLogger('django').debug('DISCONNECT on channel %s. Code: %s', self.channel_name, close_code)
        await self.channel_layer.group_discard(self.user_group, self.channel_name)

    async def task_started(self, event):
        """Echoes the task.started document."""
        await self.distribute_task_event(event)

    async def task_success(self, event):
        """Echoes the task.success document."""
        await self.distribute_task_event(event)

    async def task_cancelled(self, event):
        """Echoes the task.cancelled document."""
        await self.distribute_task_event(event)

    async def task_error(self, event):
        """Echoes the task.error document."""
        await self.distribute_task_event(event)

    async def task_badrequest(self, event):
        """Echoes the task.badrequest document."""
        await self.distribute_task_event(event)

    async def schedule_tasks(self, request_data):
        """Processes task schedule websocket requests."""
        logging.getLogger('django').debug('Processing task schedule through channel %s. Data: %s', self.channel_name, request_data)
        try:
            many_serializer = await database_sync_to_async(
                DocTaskSerializer.get_task_group_serializer)(request_data['content'])
        except exceptions.ValidationError as error:
            await self.send_bad_request_message(request_data['request_id'], error)
        else:
            await schedule_tasks(request_data['request_id'], self.scope['user'].username, *many_serializer.data)

    async def schedule_doctasks(self, request_data):
        """Processes doc-task schedule websocket requests."""
        logging.getLogger('django').debug('Processing DocTask schedule through channel %s. Data: %s', self.channel_name, request_data)
        try:
            many_serializer, doctasks = await database_sync_to_async(
                DocTaskSerializer.create_doctask_group)(request_data['content'])
        except exceptions.ValidationError as error:
            await self.send_bad_request_message(request_data['request_id'], error)
        else:
            await DocTaskScheduler.schedule_doctasks(request_data['request_id'], self.scope['user'].username, *many_serializer.data)

    @database_sync_to_async
    def clear_task_cache(self, request_data):
        """Clears a specific task cache."""
        logging.getLogger('django').debug('Processing cache clear through channel %s. Data: %s', self.channel_name, request_data)
        memory_id = request_data['content'].get('memory-id', 0)
        cache.set(self.cache_key, {
            timestamp: data for timestamp, data in cache.get(cache_key, {}).items()
            if data['memory-id'] != memory_id})

    async def distribute_task_event(self, event):
        await self.send_json(content=event['content'])
        self.cache_task_event(event)

    def cache_task_event(self, event):
        cache_key = f"{self.scope['user'].username}.task_events"
        user_task_events = cache.get(cache_key, {})
        user_task_events[str(event.get('timestamp', time.time()))] = event['content']
        cache.set(cache_key, user_task_events)

    async def receive_json(self, request_data):
        serializer = TaskRequestSerializer(data=request_data)

        try:
            serializer.is_valid(raise_exception=True)
        except exceptions.ValidationError as error:
            await self.send_bad_request_message(request_data['request_id'], error)
        else:
            await getattr(self, serializer.data['action'])(serializer.data)

    async def send_bad_request_message(self, request_id: str, error: exceptions.ValidationError):
        await self.group_send({
            'type': 'task.badrequest', 'content': {
                'details': error.get_full_details(), 'request_id': request_id, 'http_status': status.HTTP_400_BAD_REQUEST,
            }
        })

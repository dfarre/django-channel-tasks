import asyncio
import time

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.conf import settings
from django.core.cache import cache
from rest_framework import exceptions

from django_tasks.serializers import DocTaskSerializer, TaskEventSerializer
from django_tasks.task_inspector import get_coro_info
from django_tasks.task_runner import TaskRunner


class TaskEventsConsumer(AsyncJsonWebsocketConsumer):
    groups = [settings.CHANNEL_TASKS.channel_group]

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

    async def distribute_task_event(self, event):
        await self.send_json(content=event)
        self.cache_task_event(event)

    def cache_task_event(self, event):
        cache_key = f"{self.scope['user'].username}.task_events"
        user_task_events = cache.get(cache_key, {})
        user_task_events[str(event.get('timestamp', time.time()))] = event['content']
        cache.set(cache_key, user_task_events)

    def clear_task_cache(self, content):
        memory_id = content.get('memory-id', 0)
        cache_key = f"{self.scope['user'].username}.task_events"
        cache.set(cache_key, {
            timestamp: data for timestamp, data in cache.get(cache_key, {}).items()
            if data['memory-id'] != memory_id})

    async def receive_json(self, event):
        """Pocesses task schedule websocket requests, and task cache clear requests."""
        serializer = TaskEventSerializer(data=event)

        try:
            serializer.is_valid(raise_exception=True)
        except exceptions.ValidationError as error:
            await self.send_bad_request_message(error)
        else:
            if serializer.data['type'] == 'task.clear':
                self.clear_task_cache(serializer.data['content'])
            elif serializer.data['type'] == 'task.schedule':
                await self.schedule_tasks(serializer.data['content'])

    async def send_bad_request_message(self, error: exceptions.ValidationError):
        await self.channel_layer.group_send(settings.CHANNEL_TASKS.channel_group, {
            'type': 'task.badrequest', 'content': {
                'details': error.get_full_details(), 'status': 'BadRequest'
            }
        })

    async def schedule_tasks(self, content):
        """Pocesses task schedule websocket requests, and task cache clear requests."""
        try:
            many_serializer = await database_sync_to_async(DocTaskSerializer.get_task_group_serializer)(content)
        except exceptions.ValidationError as error:
            await self.send_bad_request_message(error)
        else:
            runner = TaskRunner.get()
            await asyncio.gather(*[runner.schedule(
                get_coro_info(task['registered_task'], **task['inputs']).callable(**task['inputs'])
            ) for task in many_serializer.data])

import asyncio

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from rest_framework import status

from django_tasks.drf_consumer import DrfConsumer
from django_tasks.doctask_scheduler import DocTaskScheduler
from django_tasks.serializers import DocTaskSerializer


class TasksRestConsumer(DrfConsumer, DocTaskScheduler):
    async def process_drf_response(self, drf_response):
        if drf_response.status_code == status.HTTP_201_CREATED:
            if isinstance(drf_response.data, dict):
                await self.schedule_doctask(drf_response.data)
            elif isinstance(drf_response.data, list):
                await asyncio.gather(*[self.schedule_doctask(data) for data in drf_response.data])


class TaskEventsConsumer(AsyncJsonWebsocketConsumer, DocTaskScheduler):
    groups = ['tasks']

    async def task_started(self, event):
        """Echoes the task.started document."""
        await self.handle_doctask(event['content'])
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

    async def receive_json(self, content):
        """Pocesses task schedule websocket requests."""
        await DocTaskSerializer.schedule_task_group(content)

    async def handle_doctask(self, event_content):
        doctask = await database_sync_to_async(self.retrieve_doctask)(event_content['memory-id'])
        if doctask:
            doctask.document.append(event_content)
            await doctask.asave()

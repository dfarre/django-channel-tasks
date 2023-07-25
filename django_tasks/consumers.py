import asyncio
import collections
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from rest_framework import status

from django_tasks.drf_consumer import DrfConsumer
from django_tasks.serializers import DocTaskSerializer
from django_tasks.task_runner import TaskRunner


class TasksRestConsumer(DrfConsumer):
    model = DocTaskSerializer.Meta.model
    doctask_index = collections.defaultdict(dict)

    @classmethod
    def retrieve_doctask(cls, memory_id):
        if memory_id in cls.doctask_index:
            doctask_info = cls.doctask_index[memory_id]

            try:
                return cls.model.objects.get(id=doctask_info['id'])
            except cls.model.DoesNotExist:
                count = cls.model.objects.count()
                logging.getLogger('django').error(
                    'Memorized doctask ID %s not found in DB, among %s entries.', doctask_info, count)

    async def process_drf_response(self, drf_response):
        if drf_response.status_code == status.HTTP_201_CREATED:
            if isinstance(drf_response.data, dict):
                await self.schedule_task(drf_response.data)
            elif isinstance(drf_response.data, list):
                await asyncio.gather(*[self.schedule_task(data) for data in drf_response.data])

    async def schedule_task(self, data):
        """Schedules a single task."""
        callable = DocTaskSerializer.get_coro_info(data).callable
        runner = TaskRunner.get()
        task = await runner.schedule(callable(**data['inputs']), self.store_doctask_result)
        self.doctask_index[id(task)].update({'future': task, 'id': data['id']})
        logging.getLogger('django').info('Scheduled task %s.', data)

    async def store_doctask_result(self, task_info):
        memory_id = task_info['memory-id']
        doctask = await database_sync_to_async(self.retrieve_doctask)(memory_id)

        if doctask:
            await doctask.on_completion(TaskRunner.get_task_info(self.doctask_index[memory_id]['future']))
            del self.doctask_index[memory_id]
            logging.getLogger('django').info('Stored doctask %s.', doctask)


class TaskEventsConsumer(AsyncJsonWebsocketConsumer):
    groups = ['tasks']

    async def task_started(self, event):
        """Echoes the task.started document."""
        await self.send_json(content=event["content"])

    async def task_success(self, event):
        await self.send_json(content=event['content'])

    async def task_cancelled(self, event):
        """Echoes the task.cancelled document."""
        await self.send_json(content=event['content'])

    async def task_error(self, event):
        """Echoes the task.error document."""
        await self.send_json(content=event['content'])

    async def receive_json(self, content):
        """Pocesses task schedule websocket requests."""
        await DocTaskSerializer.schedule_task_group(content)

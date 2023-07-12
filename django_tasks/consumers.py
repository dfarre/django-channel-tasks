import collections
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from django_tasks.serializers import DocTaskSerializer
from django_tasks.task_runner import TaskRunner


class TaskEventsConsumer(AsyncJsonWebsocketConsumer):
    groups = ['tasks']

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

    async def store_doctask_result(self, memory_id):
        doctask = await database_sync_to_async(self.retrieve_doctask)(memory_id)

        if doctask:
            await doctask.on_completion(TaskRunner.get_task_info(self.doctask_index[memory_id]['future']))
            del self.doctask_index[memory_id]

    async def task_started(self, event):
        """Echoes the task.started document."""
        await self.send_json(content=event["content"])

    async def task_success(self, event):
        await self.store_doctask_result(event['content']['memory-id'])
        await self.send_json(content=event['content'])

    async def task_cancelled(self, event):
        """Echoes the task.cancelled document."""
        await self.store_doctask_result(event['content']['memory-id'])
        await self.send_json(content=event['content'])

    async def task_error(self, event):
        """Echoes the task.error document."""
        await self.store_doctask_result(event['content']['memory-id'])
        await self.send_json(content=event['content'])

    async def task_schedule(self, event):
        """Schedules a single task."""
        callable = DocTaskSerializer.get_coro_info(event['content']).callable
        runner = TaskRunner.get()
        task = await runner.schedule(callable(**event['content']['inputs']))
        self.doctask_index[id(task)].update({'future': task, 'id': event['content']['doctask-id']})

    async def receive_json(self, content):
        """Pocesses task schedule websocket requests."""
        await DocTaskSerializer.schedule_task_group(content)

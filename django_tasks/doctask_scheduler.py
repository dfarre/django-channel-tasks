
import collections
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from django_tasks.serializers import DocTaskSerializer
from django_tasks.task_runner import TaskRunner


class DocTaskScheduler:
    doctask_index = collections.defaultdict(dict)
    model = DocTaskSerializer.Meta.model

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

    @classmethod
    async def store_doctask_result(cls, task_info):
        memory_id = task_info['memory-id']
        doctask = await database_sync_to_async(cls.retrieve_doctask)(memory_id)

        if doctask:
            await doctask.on_completion(TaskRunner.get_task_info(cls.doctask_index[memory_id]['future']))
            del cls.doctask_index[memory_id]
            logging.getLogger('django').info('Stored %s.', repr(doctask))

    @classmethod
    async def schedule_doctask(cls, data={}, callable=None):
        """Schedules a single task, and stores results in DB."""
        callable = callable or DocTaskSerializer.get_coro_info(data).callable
        runner = TaskRunner.get()
        task = await runner.schedule(callable(**data.get('inputs', {})), cls.store_doctask_result)
        cls.doctask_index[id(task)].update({'future': task, 'id': data.get('id')})
        logging.getLogger('django').info('Scheduled doc-task %s callable=%s.', data, callable)
        return task

    @staticmethod
    async def schedule_task(data={}, callable=None):
        """Schedules a single task without storage."""
        callable = callable or DocTaskSerializer.get_coro_info(data).callable
        runner = TaskRunner.get()
        task = await runner.schedule(callable(**data.get('inputs', {})))
        logging.getLogger('django').info('Scheduled task %s callable=%s.', data, callable)
        return task

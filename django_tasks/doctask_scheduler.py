import asyncio
import collections
import logging

from typing import Any

from channels.db import database_sync_to_async

from django_tasks.serializers import DocTaskSerializer
from django_tasks.task_runner import TaskRunner

from django_tasks.task_inspector import get_coro_info


class DocTaskScheduler:
    doctask_index: dict[int, dict[str, Any]] = collections.defaultdict(dict)
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
    async def schedule_doctask(cls, data={}, callable=None) -> asyncio.Future:
        """Schedules a single task, and stores results in DB."""
        dotted_path, inputs = data['registered_task'], data.get('inputs', {})
        callable = callable or get_coro_info(dotted_path, **inputs).callable
        runner = TaskRunner.get()
        task = await runner.schedule(callable(**inputs), cls.store_doctask_result)
        cls.doctask_index[id(task)].update({'future': task, 'id': data.get('id')})
        logging.getLogger('django').info('Scheduled doc-task %s callable=%s.', data, callable)
        return task

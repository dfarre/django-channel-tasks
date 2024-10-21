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
    def retrieve_doctask(cls, task_id: str):
        if task_id in cls.doctask_index:
            doctask_info = cls.doctask_index[task_id]

            try:
                return cls.model.objects.get(id=doctask_info['id'])
            except cls.model.DoesNotExist:
                count = cls.model.objects.count()
                logging.getLogger('django').error(
                    'Memorized doctask ID %s not found in DB, among %s entries.', doctask_info, count)

    @classmethod
    async def store_doctask_result(cls, task_id: str, task_info: dict):
        doctask = await database_sync_to_async(cls.retrieve_doctask)(task_id)

        if doctask:
            await doctask.on_completion(TaskRunner.get_task_info(cls.doctask_index[task_id]['future']))
            del cls.doctask_index[task_id]
            logging.getLogger('django').info('Stored %s.', repr(doctask))

    @classmethod
    async def schedule_doctask(cls, task_id: str, user_name: str, data: dict) -> asyncio.Future:
        """Schedules a single task, and stores results in DB."""
        dotted_path, inputs = data['registered_task'], data.get('inputs', {})
        callable = get_coro_info(dotted_path, **inputs).callable
        runner = TaskRunner.get()
        task = await runner.schedule(
            callable(**inputs), cls.store_doctask_result, task_id=task_id, user_name=user_name)
        cls.doctask_index[task_id].update({'future': task, 'id': data['id']})
        logging.getLogger('django').info('Scheduled doc-task %s callable=%s.', data, callable)
        return task

    @classmethod
    async def schedule_doctasks(cls, request_id: str, user_name: str, *task_data) -> asyncio.Future:
        future = await asyncio.gather(*[
            cls.schedule_doctask(f'{request_id}.{n}', user_name, data) for n, data in enumerate(task_data)
        ])
        return future


async def schedule_tasks(request_id: str, user_name: str, *task_data) -> asyncio.Future:
    runner = TaskRunner.get()
    future = await asyncio.gather(*[runner.schedule(
        get_coro_info(task['registered_task'], **task['inputs']).callable(**task['inputs']),
        task_id=f'{request_id}.{n}', user_name=user_name,
    ) for n, task in enumerate(task_data)])
    return future

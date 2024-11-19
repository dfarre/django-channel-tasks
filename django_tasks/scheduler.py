"""
This module provides the tools for scheduling arrays of tasks, with or without task result storage.
"""
import asyncio
import logging

from asgiref.sync import sync_to_async
from typing import Optional

from django_tasks import models
from django_tasks.task_runner import TaskRunner
from django_tasks.task_inspector import get_task_coro
from django_tasks.typing import TaskStatusJSON, TaskJSON, DocTaskJSON


class DocTaskScheduler:
    """
    Static class that manages all doc-task runs, capable of scheduling, as requested by a Django user,
    arrays of tasks that are documented in database as :py:class:`django_tasks.models.DocTask` instances.
    """
    model = models.DocTask

    #: Will hold all running doc-task database IDs by task ID
    doctask_index: dict[str, int] = {}

    @classmethod
    def retrieve_doctask(cls, task_id: str) -> Optional[models.DocTask]:
        if task_id in cls.doctask_index:
            doctask_id = cls.doctask_index[task_id]
            try:
                return cls.model.objects.get(pk=doctask_id)
            except cls.model.DoesNotExist:
                count = cls.model.objects.count()
                logging.getLogger('django').error(
                    'Memorized doctask ID %s not found in DB, among %s entries.', doctask_id, count)
        return None

    @classmethod
    async def store_doctask_result(cls, task_id: str, task_info: TaskStatusJSON) -> None:
        doctask = await sync_to_async(cls.retrieve_doctask)(task_id)

        if doctask:
            await doctask.on_completion(task_info)
            del cls.doctask_index[task_id]
            logging.getLogger('django').info('Stored %s.', repr(doctask))

    @classmethod
    async def schedule_doctask(cls, task_id: str, user_name: str, valid_data: DocTaskJSON) -> asyncio.Future:
        """Schedules a single task, and stores results in DB."""
        task_coro = get_task_coro(valid_data['registered_task'], valid_data['inputs'])
        runner = TaskRunner.get()
        task = await runner.schedule(
            task_coro.coroutine, cls.store_doctask_result, task_id=task_id, user_name=user_name
        )
        cls.doctask_index[task_id] = valid_data['id']
        logging.getLogger('django').info('Scheduled doc-task %s callable=%s.', valid_data, task_coro.callable)
        return task

    @classmethod
    async def schedule_doctasks(cls, request_id: str, user_name: str, *valid_data: DocTaskJSON) -> list[asyncio.Future]:
        futures = await asyncio.gather(*[
            cls.schedule_doctask(f'{request_id}.{n}', user_name, data) for n, data in enumerate(valid_data)
        ])
        return futures


async def schedule_tasks(request_id: str, user_name: str, *valid_data: TaskJSON) -> list[asyncio.Future]:
    """Schedules an array of tasks as requested by a Django user."""
    runner = TaskRunner.get()
    futures = await asyncio.gather(*[runner.schedule(
        get_task_coro(dat['registered_task'], dat['inputs']).coroutine,
        task_id=f'{request_id}.{n}', user_name=user_name,
    ) for n, dat in enumerate(valid_data)])
    return futures

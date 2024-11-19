"""This module provides the :py:class:`django_tasks.task_runner.TaskRunner` class."""
from __future__ import annotations

import asyncio
import inspect
import logging
import time
import threading

from typing import Callable, Coroutine

from channels.layers import get_channel_layer
from rest_framework import status
from django.conf import settings

from django_tasks.task_cache import TaskCache
from django_tasks.typing import TaskStatusJSON, TaskMessageJSON


class TaskRunner:
    """
    Singleton class in charge of scheduling background task runs with `asyncio`, in a dedicated (worker) thread,
    and of broadcasting the task states and results through a configured channel layer.

    The worker thread is a daemon thread running a separate (worker) event loop; that worker loop runs
    all the scheduled background tasks concurrently.

    Usage, in async context, is as follows::

        runner = TaskRunner.get()
        future = await runner.schedule(coroutine, *callbacks, task_id='<UniversalID>', user_name='<DjangoUsername>')

    See the :py:meth:`TaskRunner.schedule` method.
    """

    #: Will hold the list of existing :py:class:`TaskRunner` instances, containing at most one instance.
    instances: list[TaskRunner] = []

    @classmethod
    def get(cls) -> TaskRunner:
        """
        Returns the last instance created, a new one if necessary, and ensures that its worker thread is alive.
        """
        if not cls.instances:
            cls()

        cls.instances[-1].ensure_alive()

        logging.getLogger('django').debug('Using task runner: %s.', cls.instances[-1])
        return cls.instances[-1]

    def __init__(self):
        caller_frame = inspect.stack()[1][0]
        caller_name = (f"{caller_frame.f_locals['cls'].__name__}.{caller_frame.f_code.co_name}"
                       if 'cls' in caller_frame.f_locals else caller_frame.f_code.co_name)
        assert caller_name == 'TaskRunner.get', (
                f"TaskRunner instances must be created by its 'get' classmethod (so not by '{caller_name}')")

        self.worker_event_loop = asyncio.new_event_loop()
        self.worker_event_loop.set_debug(settings.DEBUG)
        self.worker_thread = threading.Thread(target=self.worker_event_loop.run_forever, daemon=True)
        self.__class__.instances.append(self)
        logging.getLogger('django').debug('New task runner: %s.', self)

    def __str__(self) -> str:
        return f'loop={self.worker_event_loop}, thread={self.worker_thread}'

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__}: {self}>'

    def ensure_alive(self):
        """Ensures the worker thread is alive."""
        if not self.worker_thread.is_alive():
            self.worker_thread.start()

    def run_coroutine(self, coroutine: Coroutine) -> asyncio.Future:
        """Runs the given coroutine thread-safe in the worker loop."""
        return asyncio.wrap_future(asyncio.run_coroutine_threadsafe(coroutine, self.worker_event_loop))

    def run_on_task_info(self,
                         async_callback: Callable[[str, TaskStatusJSON], Coroutine],
                         task_id: str,
                         task: asyncio.Future) -> asyncio.Future:
        """
        Runs the given async callback on the task result, taking the task ID and yielded task data as arguments.
        """
        return self.run_coroutine(async_callback(task_id, self.get_task_status(task)))

    async def schedule(self,
                       coroutine: Coroutine,
                       *coro_callbacks: Callable[[str, TaskStatusJSON], Coroutine],
                       task_id: str = '',
                       user_name: str = '') -> asyncio.Future:
        """
        Schedules the given coroutine and (optional) callbacks to run immediately in the worker thread,
        and notifies the specified user of the task state.

        :param coroutine: Coroutine of the main task to run.
        :param coro_callbacks: Sequence of async callbacks that will run just after the main task has finished,
            taking as arguments the task ID and the yielded task data.
        :param task_id: A universally unique identifier of the main task.
        :param user_name: A Django user name.

        Note that `task_id`, `user_name` are optional parameters here; this class is not responsible
        of validating them.
        """
        task_name = coroutine.__name__
        task = self.run_coroutine(coroutine)
        await self.broadcast_task(task_name, task_id, user_name, task)

        task.add_done_callback(lambda tk: self.run_coroutine(self.broadcast_task(task_name, task_id, user_name, tk)))

        for coro_callback in coro_callbacks:
            task.add_done_callback(lambda tk: self.run_on_task_info(coro_callback, task_id, tk))

        return task

    @classmethod
    async def broadcast_task(cls, name: str, task_id: str, user_name: str, task: asyncio.Future):
        """Caches the task information, and sends it to all consumers to which the user is connected,
        specifying a message type per task status.

        :param name: The name of the task coroutine.
        :param task_id: The universally unique identifier of the task.
        :param user_name: The name of the Django user that will get noticed.
        :param task: The task future.

        Note that this class is not responsible of validating these parameters.
        """
        status_data = cls.get_task_status(task)
        status_data['registered_task'] = name
        task_info: TaskMessageJSON = {'task_id': task_id, 'detail': status_data}

        user_task_cache = TaskCache(user_name)
        user_task_cache.cache_task_event(task_id, task_info)

        task_event = {'type': f"task.{status_data['status'].lower()}", 'content': task_info, 'timestamp': time.time()}
        channel_layer = get_channel_layer()
        await channel_layer.group_send(f'{user_name}_{settings.CHANNEL_TASKS.channel_group}', task_event)

    @staticmethod
    def get_task_status(task: asyncio.Future) -> TaskStatusJSON:
        """Extracts and returns the corresponding task status and result (if any result)."""
        task_info: TaskStatusJSON = {'http_status': status.HTTP_200_OK}

        if not task.done():
            task_info['status'] = 'Started'
        elif task.cancelled():
            task_info['status'] = 'Cancelled'
        elif task.exception():
            task_info.update({'status': 'Error',
                              'exception-repr': repr(task.exception())})
        else:
            task_info.update({'status': 'Success', 'output': task.result()})

        return task_info

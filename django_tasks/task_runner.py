from __future__ import annotations

import asyncio
import logging
import threading

from typing import Any, Callable, Coroutine

from channels.layers import get_channel_layer


class TaskRunner:
    """
    Class in charge of in-memory handling of `asyncio` background tasks, with a worker thread per instance.
    """
    _instances: list[TaskRunner] = []

    @classmethod
    def get(cls) -> TaskRunner:
        """
        Returns the last instance created, a new one if necessary, and ensures that its worker thread is alive.
        """
        if not cls._instances:
            cls()

        cls._instances[-1].ensure_alive()

        logging.getLogger('django').debug('Using task runner: %s.', cls._instances[-1])
        return cls._instances[-1]

    def __init__(self):
        self.event_loop = asyncio.new_event_loop()
        self.worker_thread = threading.Thread(target=self.event_loop.run_forever, daemon=True)
        self.__class__._instances.append(self)
        logging.getLogger('django').debug('New task runner: %s.', self)

    def __str__(self):
        return f'loop={self.event_loop}, worker={self.worker_thread}'

    def __repr__(self):
        return f'<{self.__class__.__name__}: {self}>'

    def ensure_alive(self):
        """Ensures the worker thread is alive."""
        if not self.worker_thread.is_alive():
            self.worker_thread.start()

    def run_coroutine(self, coroutine: Coroutine) -> asyncio.Future:
        """Runs the given `coroutine` thread-safe in the loop."""
        return asyncio.wrap_future(asyncio.run_coroutine_threadsafe(coroutine, self.event_loop))

    def run_on_task_info(self,
                         async_callback: Callable[[dict[str, Any]], Coroutine],
                         task: asyncio.Future) -> asyncio.Future:
        """Runs the `async_callback` taking the task info as the argument."""
        return self.run_coroutine(async_callback(self.get_task_info(task)))

    async def schedule(self,
                       coroutine: Coroutine,
                       *coro_callbacks: Callable[[dict[str, Any]], Coroutine]) -> asyncio.Future:
        task_name = coroutine.__name__
        task = self.run_coroutine(coroutine)
        await self.broadcast_task(task_name, task)

        task.add_done_callback(lambda tk: self.run_coroutine(self.broadcast_task(task_name, tk)))

        for coro_callback in coro_callbacks:
            task.add_done_callback(lambda tk: self.run_on_task_info(coro_callback, tk))

        return task

    @classmethod
    async def broadcast_task(cls, name: str, task: asyncio.Future):
        """
        Sends the task info to the 'tasks' group of consumers, specifying a message type per task status.
        """
        task_info = cls.get_task_info(task)
        task_info['registered_task'] = name
        message_type = f"task.{task_info['status'].lower()}"
        channel_layer = get_channel_layer()
        await channel_layer.group_send("tasks", {'type': message_type, 'content': task_info})

    @staticmethod
    def get_task_info(task: asyncio.Future) -> dict[str, Any]:
        """Extracts and returns the corresponding task info, with the current task status."""
        task_info: dict[str, Any] = {'memory-id': id(task)}

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

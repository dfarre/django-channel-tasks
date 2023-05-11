import asyncio
import threading

from typing import Coroutine

from channels.layers import get_channel_layer


class TaskRunnerUsageError(Exception):
    """To be raised on bad uses of the `TaskRunner` class."""


class TaskRunner:
    """
    Class in charge of in-memory handling of `asyncio` background tasks, with a worker thread per instance.
    """
    _instances = []

    @classmethod
    def get(cls):
        if not cls._instances:
            cls._instances.append(cls())

        cls._instances[-1].ensure_alive()

        return cls._instances[-1]

    def __init__(self, *args, **kwargs):
        self.event_loop = asyncio.new_event_loop()
        self.worker_thread = threading.Thread(target=self.run_loop_forever, daemon=True)
        self.running_tasks = {}

    def run_loop_forever(self):
        asyncio.set_event_loop(self.event_loop)
        self.event_loop.run_forever()

    def ensure_alive(self):
        if not self.worker_thread.is_alive():
            self.worker_thread.start()

    def run_coroutine(self, coroutine: Coroutine):
        return asyncio.wrap_future(asyncio.run_coroutine_threadsafe(coroutine, self.event_loop))

    def run_on_task_info(self, async_callback, task: asyncio.Future):
        """Runs the `async_callback` taking the task info as the argument."""
        self.run_coroutine(async_callback(self.get_task_info(task)))

    async def broadcast_task(self, task: asyncio.Future):
        task_info = self.get_task_info(task)
        message_type = f"task.{task_info['status'].lower()}"
        channel_layer = get_channel_layer()
        await channel_layer.group_send("tasks", {'type': message_type, 'content': task_info})

    def update_task_info(self, task: asyncio.Future):
        task_info = self.get_task_info(task)

        if task.cancelled():
            task_info['status'] = 'Cancelled'
        elif task.exception():
            task_info.update({'status': 'Error',
                              'exception-type': task.exception().__class__.__name__,
                              'exception-text': str(task.exception())})
        else:
            task_info.update({'status': 'Success', 'output': task.result()})

    async def schedule(self, coroutine: Coroutine, *async_callbacks):
        task = self.run_coroutine(coroutine)
        self.running_tasks[id(task)] = {'status': 'Started', 'memory-id': id(task)}
        task.add_done_callback(self.update_task_info)
        task.add_done_callback(lambda tk: self.run_coroutine(self.broadcast_task(tk)))

        for callback in async_callbacks:
            task.add_done_callback(lambda tk: self.run_on_task_info(callback, tk))

        await self.broadcast_task(task)

        return task

    def get_task_info(self, task: asyncio.Future):
        return self.running_tasks[id(task)]

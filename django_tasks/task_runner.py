import asyncio
import threading

from typing import Coroutine, Dict, Any

from channels.layers import get_channel_layer

from django_tasks import models


class TaskRunnerUsageError(Exception):
    """To be raised on bad uses of the `TaskRunner` class."""


class TaskRunner:
    """
    Class in charge of in-memory handling of `asyncio` background tasks,
    with a worker thread per instance.
    """
    running_tasks: Dict[str, Any]
    event_loop: asyncio.SelectorEventLoop
    worker_thread: threading.Thread

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

    def on_completion(self, task: asyncio.Future):
        """
        The 'task done' callback, it populates the result and completion time in DB,
        and it broadcasts a task-done websocket message.
        """
        self.update_task_info(task)
        self.run_coroutine(self.save_task_info(task))
        self.broadcast_task_done(task)

    async def save_task_info(self, task: asyncio.Future):
        scheduled_task = await models.ScheduledTask.objects.aget(task_id=id(task))
        await scheduled_task.on_completion(self.get_task_info(task))

    def broadcast_task_done(self, task: asyncio.Future):
        channel_layer = get_channel_layer()
        self.run_coroutine(channel_layer.group_send("tasks", {
            "type": "task.done",
            "content": self.get_task_info(task),
        }))

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

    async def schedule(self, coroutine: Coroutine):
        task = self.run_coroutine(coroutine)
        self.running_tasks[id(task)] = {}
        task.add_done_callback(self.on_completion)

        return task

    def get_task_info(self, task: asyncio.Future):
        return self.running_tasks[id(task)]

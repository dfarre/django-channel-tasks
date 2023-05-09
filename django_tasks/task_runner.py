import asyncio
import datetime
import logging
import threading

from typing import Coroutine, Dict, Any


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
    logger = logging.getLogger("task-runner")

    def __init__(self, *args, **kwargs):
        self.event_loop = asyncio.new_event_loop()
        self.worker_thread = threading.Thread(target=self.run_loop_forever, daemon=True)
        self.running_tasks = {}

    def run_loop_forever(self):
        asyncio.set_event_loop(self.event_loop)
        self.event_loop.run_forever()

    def on_completion(self, task: asyncio.Future):
        """The 'task done' callback, it populates the result and completion time."""
        task_info = self.get_task_info(task)
        task_info['completed_at'] = datetime.datetime.utcnow()

        if task.cancelled():
            task_info['status'] = 'Cancelled'
        elif task.exception():
            task_info.update({'status': 'Error',
                              'exception-type': task.exception().__class__.__name__,
                              'exception-text': str(task.exception())})
        else:
            task_info.update({'status': 'Success', 'output': task.result()})

        self.logger.info('Done %s %s.', task, task_info)

    async def schedule(self, coroutine: Coroutine):
        task = asyncio.wrap_future(asyncio.run_coroutine_threadsafe(coroutine, self.event_loop))
        self.running_tasks[id(task)] = {'started_at': datetime.datetime.utcnow()}
        task.add_done_callback(self.on_completion)

        return task

    def get_task_info(self, task: asyncio.Future):
        return self.running_tasks[id(task)]

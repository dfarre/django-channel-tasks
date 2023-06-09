import datetime
import json

from typing import Callable

from django.db.models import Model, CharField, DateTimeField, JSONField

from django_tasks.task_runner import TaskRunner


class DefensiveJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        try:
            return super().default(obj)
        except TypeError:
            return repr(obj)


class DocTask(Model):
    """Stored information of a task execution."""
    name: CharField = CharField(max_length=80)
    scheduled_at: DateTimeField = DateTimeField(default=datetime.datetime.now)
    completed_at: DateTimeField = DateTimeField(null=True)
    inputs: JSONField = JSONField(null=False, default=dict, encoder=DefensiveJsonEncoder)
    document: JSONField = JSONField(null=True)

    def __str__(self):
        return (f'Task completed at {self.completed_at}. Took {self.duration}' if self.completed_at
                else f'Running for {self.duration}')

    @property
    def duration(self):
        return (self.completed_at if self.completed_at else datetime.datetime.now()) - self.scheduled_at

    @classmethod
    async def schedule(cls, callable: Callable, **inputs):
        """Creates a `DocTask` instance to run the given function with given arguments.
        The resulting `task` (actually an `asyncio.Future`) should return a JSON-serializable object
        as result -task document- to be stored; `inputs` should be JSON-serializable as well,
        and valid keyword arguments to `callable`.
        """
        scheduled_task = cls(name=callable.__name__, inputs=inputs)
        runner = TaskRunner.get()
        task = await runner.schedule(callable(**inputs), scheduled_task.on_completion)
        await scheduled_task.asave()
        return scheduled_task, task

    async def on_completion(self, task_info):
        self.completed_at = datetime.datetime.now()
        self.document = task_info
        await self.asave()

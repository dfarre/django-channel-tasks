import datetime

from typing import Callable

from django.db.models import Model, CharField, PositiveBigIntegerField, DateTimeField, JSONField

from django_tasks.task_runner import TaskRunner


class ScheduledTask(Model):
    """Information of each execution."""
    name: CharField = CharField(max_length=80)
    task_id: PositiveBigIntegerField = PositiveBigIntegerField()
    scheduled_at: DateTimeField = DateTimeField(default=datetime.datetime.now)
    completed_at: DateTimeField = DateTimeField(null=True)
    inputs: JSONField = JSONField(null=False, default=dict)
    document: JSONField = JSONField(null=True)

    def __str__(self):
        text = f'Task {self.task_id}'
        return text if not self.completed_at else text + f'. Completed at {self.completed_at}'

    @property
    def duration(self):
        return (self.completed_at if self.completed_at else datetime.datetime.now()) - self.scheduled_at

    @classmethod
    async def schedule(cls, callable: Callable, **inputs):
        """Creates a `ScheduledTask` instance to run the given function with given arguments.
        The resulting `task` (actually an `asyncio.Future`) should return a JSON-serializable object
        as result -task document- to be stored; `inputs` should be JSON-serializable as well,
        and valid keyword arguments to `callable`.
        """
        scheduled_task = cls(name=callable.__name__, inputs=inputs)
        runner = TaskRunner.get()
        task = await runner.schedule(callable(**inputs), scheduled_task.on_completion)
        scheduled_task.task_id = id(task)
        await scheduled_task.asave()
        return scheduled_task

    async def on_completion(self, task_info):
        self.completed_at = datetime.datetime.now()
        self.document = task_info
        await self.asave()

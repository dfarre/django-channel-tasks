import datetime

from django.db import models


class ScheduledTask(models.Model):
    """Information of each execution."""
    name = models.CharField(max_length=80)
    task_id = models.PositiveBigIntegerField()
    scheduled_at = models.DateTimeField(default=datetime.datetime.now)
    completed_at = models.DateTimeField(null=True)
    inputs = models.JSONField(null=False, default=dict)
    document = models.JSONField(null=True)

    def __str__(self):
        text = f'Task {self.task_id}'
        return text if not self.completed_at else text + f'. Completed at {self.completed_at}'

    @classmethod
    async def schedule(cls, runner, callable, **inputs):
        """Creates a `ScheduledTask` instance to run the given function with given arguments.
        The resulting `task` (actually an `asyncio.Future`) should return a JSON-serializable object
        as result -task document- to be stored; `inputs` should be JSON-serializable as well,
        and valid keyword arguments to `callable`.
        """
        task = await runner.schedule(callable(**inputs))
        scheduled_task = cls(task_id=id(task), name=callable.__name__, inputs=inputs)
        await scheduled_task.asave()
        return scheduled_task

    async def on_completion(self, task_info):
        self.completed_at = datetime.datetime.now()
        self.document = task_info
        await self.asave()

import datetime

from django.db import models


class ScheduledTask(models.Model):
    """Information of each execution."""
    name = models.CharField(max_length=80)
    task_id = models.PositiveBigIntegerField()
    scheduled_at = models.DateTimeField(default=datetime.datetime.now)
    completed_at = models.DateTimeField(null=True)
    document = models.JSONField(null=True)

    def __str__(self):
        text = f'Task {self.task_id}'
        return text if not self.completed_at else text + f'. Completed at {self.completed_at}'

    @classmethod
    async def schedule(cls, runner, callable, *args, **kwargs):
        """Creates a `ScheduledTask` instance to run the given function with given arguments.
        The resulting `task` (actually an `asyncio.Future`) should return a JSON-serializable object
        as result -task document- to be stored.
        """
        task = await runner.schedule(callable(*args, **kwargs))
        scheduled_task = cls(task_id=id(task), name=callable.__name__)
        task.add_done_callback(scheduled_task.on_completion)
        await scheduled_task.asave()
        return scheduled_task

    def on_completion(self, task):
        """The 'task done' callback.
        It populates the result and completion time. Since this is called from an async context,
        the instance is saved in a thread as required by Django."""
        self.completed_at = datetime.datetime.now()

        if task.cancelled():
            self.document = {'status': 'Cancelled'}
        elif task.exception():
            self.document = {'status': 'Error',
                             'exception-type': task.exception().__class__.__name__,
                             'exception-text': str(task.exception())}
        else:
            self.document = {'status': 'Ok', 'output': task.result()}

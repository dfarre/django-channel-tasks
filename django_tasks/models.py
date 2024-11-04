import inspect
import json
import logging

from typing import Callable

from django.db.models import Model, CharField, DateTimeField, JSONField, ForeignKey, CASCADE
from django.utils import timezone


class DefensiveJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        try:
            return super().default(obj)
        except TypeError:
            return repr(obj)


class RegisteredTask(Model):
    """Specifies a trusted coroutine function to run as task."""
    dotted_path: CharField = CharField(max_length=80, unique=True)

    def __str__(self):
        return self.dotted_path

    @classmethod
    def register(cls, callable: Callable) -> Callable:
        """
        Registers the given coroutine function in database.

        Usage is as follows::

            RegisteredTask = apps.get_model('django_tasks', 'RegisteredTask')
            RegisteredTask.register(new_coroutine_function)

        after Django model setup.

        Raises `AssertionError` if `callable` is not a coroutine function.
        """
        assert inspect.iscoroutinefunction(callable), 'The function must be a coroutine'

        instance, created = cls.objects.get_or_create(
            dotted_path=f'{inspect.getmodule(callable).__spec__.name}.{callable.__name__}'
        )
        msg = 'Registered new task %s' if created else 'Task %s already registered'
        logging.getLogger('django').info(msg, instance)

        return callable


class DocTask(Model):
    """Stored information of a task execution."""
    registered_task: ForeignKey = ForeignKey(RegisteredTask, on_delete=CASCADE)
    scheduled_at: DateTimeField = DateTimeField(default=timezone.now)
    completed_at: DateTimeField = DateTimeField(null=True)
    inputs: JSONField = JSONField(default=dict, encoder=DefensiveJsonEncoder)
    document: JSONField = JSONField(default=list, encoder=DefensiveJsonEncoder)

    def __str__(self):
        return f'Doc-task {self.pk}, ' + (
            f'completed at {self.completed_at}, took {self.duration}' if self.completed_at
            else f'running for {self.duration}')

    @property
    def duration(self):
        return (self.completed_at if self.completed_at else timezone.now()) - self.scheduled_at

    async def on_completion(self, task_info):
        self.completed_at = timezone.now()
        self.document.append(task_info)
        await self.asave()

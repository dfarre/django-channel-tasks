import datetime
import json

from django.db.models import Model, CharField, DateTimeField, JSONField, ForeignKey, CASCADE


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


class DocTask(Model):
    """Stored information of a task execution."""
    registered_task: ForeignKey = ForeignKey(RegisteredTask, on_delete=CASCADE)
    scheduled_at: DateTimeField = DateTimeField(default=datetime.datetime.now)
    completed_at: DateTimeField = DateTimeField(null=True)
    inputs: JSONField = JSONField(default=dict, encoder=DefensiveJsonEncoder)
    document: JSONField = JSONField(default=list, encoder=DefensiveJsonEncoder)

    def __str__(self):
        return f'Doc-task {self.pk}, ' + (
            f'completed at {self.completed_at}, took {self.duration}' if self.completed_at
            else f'running for {self.duration}')

    @property
    def duration(self):
        return (self.completed_at if self.completed_at else datetime.datetime.now()) - self.scheduled_at

    async def on_completion(self, task_info):
        self.completed_at = datetime.datetime.now()
        self.document.append(task_info)
        await self.asave()

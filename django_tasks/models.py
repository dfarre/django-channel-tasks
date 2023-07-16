import datetime
import json

from django.db.models import Model, CharField, DateTimeField, JSONField


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

    async def on_completion(self, task_info):
        self.completed_at = datetime.datetime.now()
        self.document = task_info
        await self.asave()


from typing import Callable
from rest_framework import exceptions, serializers

from django_tasks import models, tasks
from django_tasks.task_runner import TaskRunner


def clean_task_name(name: str) -> Callable:
    reduced_name = name.strip()
    callable = getattr(tasks, reduced_name, None)

    if callable is None:
        raise exceptions.ValidationError(f"No task function '{reduced_name}'")

    return callable


class ScheduledTaskSerializer(serializers.ModelSerializer):
    name = serializers.CharField(validators=[clean_task_name])

    class Meta:
        model = models.ScheduledTask
        fields = '__all__'
        read_only_fields = ('scheduled_at', 'completed_at', 'document', 'task_id')

    async def schedule_task(self, task_runner: TaskRunner):
        task_callable = clean_task_name(self.data['name'])

        self.instance = await self.Meta.model.schedule(task_runner, task_callable)

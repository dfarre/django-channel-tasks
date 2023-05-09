from asgiref.sync import async_to_sync
import inspect
import importlib
from typing import Callable
from rest_framework import exceptions, serializers

from django.conf import settings

from django_tasks import models


def clean_task_name(name: str) -> Callable:
    method_name = name.strip()
    module_names = settings.DJANGO_TASKS.get('coroutine_modules', [])

    for module_name in module_names:
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            pass
        else:
            callable = getattr(module, method_name, None)

            if inspect.iscoroutinefunction(callable):
                return callable


class ScheduledTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ScheduledTask
        fields = '__all__'
        read_only_fields = ('scheduled_at', 'completed_at', 'document', 'task_id')

    @property
    def task_runner(self):
        runner = self.context['view'].task_runner
        runner.ensure_alive()
        return runner

    async def schedule_task(self, validated_data):
        instance = await self.Meta.model.schedule(
            self.task_runner, self.context['task_callable'], **validated_data['inputs']
        )
        return instance

    def validate(self, attrs):
        self.context['task_callable'] = clean_task_name(attrs['name'])

        if self.context['task_callable'] is None:
            raise exceptions.ValidationError({'name': "No task coroutine found."})

        signature = inspect.signature(self.context['task_callable'])
        unknown_params = set(attrs['inputs']) - set(signature.parameters)

        if unknown_params:
            raise exceptions.ValidationError({'inputs': f'Unknown parameters {unknown_params}'})

        return attrs

    def create(self, validated_data):
        return async_to_sync(self.schedule_task)(validated_data)

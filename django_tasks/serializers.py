import asyncio

from asgiref.sync import async_to_sync

from typing import Any

from rest_framework import exceptions, serializers

from django_tasks import models, task_inspector, task_runner


class ScheduledTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ScheduledTask
        read_only_fields = ('scheduled_at', 'completed_at', 'document', 'task_id')
        fields = ('name', 'inputs', *read_only_fields)

    async def schedule_task(self, validated_data: dict[str, Any]) -> models.ScheduledTask:
        instance = await self.Meta.model.schedule(self.context['task_callable'], **validated_data['inputs'])
        return instance

    async def schedule(self) -> asyncio.Future:
        runner = task_runner.TaskRunner.get()
        task = await runner.schedule(self.context['task_callable'](**self.data['inputs']))
        return task

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        coroutine_info = task_inspector.TaskCoroInfo(attrs['name'])
        self.context['task_callable'] = coroutine_info.coroutine

        if self.context['task_callable'] is None:
            raise exceptions.ValidationError({'name': "No task coroutine found."})

        input_keys = set(attrs['inputs'])
        required_keys, optional_keys = coroutine_info.parameter_keys
        errors = []

        missing_keys = required_keys - input_keys

        if missing_keys:
            errors.append(f'Missing required parameters {missing_keys}.')

        unknown_keys = input_keys - required_keys - optional_keys

        if unknown_keys:
            errors.append(f'Unknown parameters {unknown_keys}.')

        if errors:
            raise exceptions.ValidationError({'inputs': errors})

        return attrs

    def create(self, validated_data: dict[str, Any]) -> models.ScheduledTask:
        return async_to_sync(self.schedule_task)(validated_data)

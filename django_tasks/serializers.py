from asgiref.sync import async_to_sync

from typing import Callable, Optional, Any

from rest_framework import exceptions, serializers

from django_tasks import models
from django_tasks import task_inspector


class DocTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.DocTask
        read_only_fields = ('scheduled_at', 'completed_at', 'document')
        fields = ('name', 'inputs', *read_only_fields)

    @property
    def callable(self) -> Optional[Callable]:
        task_info = self.context.get('task_info')
        return task_info.callable if task_info else None

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        self.context['task_info'] = task_inspector.TaskCoroInfo(attrs['name'], **attrs['inputs'])
        errors = self.context['task_info'].task_call_errors

        if errors:
            raise exceptions.ValidationError(errors)

        return attrs

    def create(self, validated_data: dict[str, Any]) -> models.DocTask:
        return async_to_sync(self._schedule_task)(validated_data)

    async def _schedule_task(self, validated_data: dict[str, Any]) -> models.DocTask:
        instance, _ = await self.Meta.model.schedule(self.callable, **validated_data['inputs'])
        return instance

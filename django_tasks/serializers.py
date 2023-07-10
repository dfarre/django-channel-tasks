import asyncio
from asgiref.sync import async_to_sync

from typing import Callable, Optional, Any

from rest_framework import exceptions, serializers

from django_tasks import models
from django_tasks import task_inspector
from django_tasks import task_runner


class DocTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.DocTask
        read_only_fields = ('scheduled_at', 'completed_at', 'document')
        fields = ('name', 'inputs', *read_only_fields)

    @classmethod
    async def schedule_task_group(cls, json_content):
        many_serializer = cls(data=json_content, many=True)
        many_serializer.is_valid(raise_exception=True)
        runner = task_runner.TaskRunner.get()
        tasks = await asyncio.gather(*[
            runner.schedule(many_serializer.child.get_coro_info(task).callable(**task['inputs']))
            for task in many_serializer.data]
        )
        return many_serializer, tasks

    async def schedule_doctask(self, validated_data: dict[str, Any]):
        instance, task = await self.Meta.model.schedule(
            self.get_coro_info(validated_data).callable, **validated_data['inputs'])
        return instance, task

    @classmethod
    async def schedule_doctask_group(cls, json_content, *args, **kwargs):
        many_serializer = cls(data=json_content, many=True, *args, **kwargs)
        many_serializer.is_valid(raise_exception=True)
        doctasks = await asyncio.gather(*[
            cls.Meta.model.schedule(cls.get_coro_info(task_data).callable, **task_data['inputs'])
            for task_data in many_serializer.data]
        )
        return many_serializer, doctasks

    @staticmethod
    def get_coro_info(attrs: dict[str, Any]) -> Optional[Callable]:
        coro_info = task_inspector.TaskCoroInfo(attrs['name'], **attrs['inputs'])
        errors = coro_info.task_call_errors

        if errors:
            raise exceptions.ValidationError(errors)

        return coro_info

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        self.context['coro_info'] = self.get_coro_info(attrs)

        return attrs

    def create(self, validated_data: dict[str, Any]) -> models.DocTask:
        instance, _ = async_to_sync(self.schedule_doctask)(validated_data)
        return instance

import asyncio

from typing import Callable, Optional, Any

from rest_framework import exceptions, serializers

from django_tasks import models
from django_tasks import task_inspector
from django_tasks import task_runner


class DocTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.DocTask
        read_only_fields = ('id', 'scheduled_at', 'completed_at', 'document')
        fields = ('name', 'inputs', *read_only_fields)

    @classmethod
    async def schedule_task_group(cls, json_content, *args, **kwargs):
        many_serializer = cls(data=json_content, *args, many=True, **kwargs)
        many_serializer.is_valid(raise_exception=True)
        runner = task_runner.TaskRunner.get()
        tasks = await asyncio.gather(*[
            runner.schedule(many_serializer.child.get_coro_info(task).callable(**task['inputs']))
            for task in many_serializer.data
        ])
        return many_serializer, tasks

    @classmethod
    def create_doctask_group(cls, json_content, *args, **kwargs):
        many_serializer = cls(data=json_content, many=True, *args, **kwargs)
        many_serializer.is_valid(raise_exception=True)
        doctasks = many_serializer.save()

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
        """Creates a `DocTask` instance to run the specified function with given arguments.
        The resulting task (actually an `asyncio.Future`) should return a JSON-serializable object
        as result -task document- to be stored; 'inputs' should be valid keyword arguments to `callable`.
        """
        return self.Meta.model.objects.create(name=validated_data['name'], inputs=validated_data['inputs'])

"""This module provides the DRF serializers, which are employed in web-socket and HTTP endpoints."""
from __future__ import annotations
from typing import Any

from rest_framework.serializers import ChoiceField, JSONField, SlugRelatedField, Serializer, ModelSerializer

from django_tasks import models

from django_tasks.task_inspector import get_task_coro
from django_tasks.typing import TaskJSON


class TaskRequestSerializer(Serializer):
    """Serializer of generic task request data."""
    action = ChoiceField(choices=['schedule_tasks', 'schedule_doctasks', 'clear_task_cache'])
    content = JSONField(default=None)


class DocTaskSerializer(ModelSerializer):
    """Model serializer for the :py:class:`django_tasks.models.DocTask` model."""
    registered_task = SlugRelatedField(
        slug_field='dotted_path', queryset=models.RegisteredTask.objects.all())

    class Meta:
        model = models.DocTask
        read_only_fields = ('id', 'scheduled_at', 'completed_at', 'document')
        fields = ('registered_task', 'inputs', *read_only_fields)

    @classmethod
    def get_task_group_serializer(cls, json_content: list[TaskJSON], *args, **kwargs) -> DocTaskSerializer:
        """
        Creates and returns a valid serializer instance for the given array of doc-task data.
        Raises a :py:class:`rest_framework.exceptions.ValidationError` on failure.
        """
        kwargs.update(dict(many=True, data=json_content))
        many_serializer = cls(*args, **kwargs)
        many_serializer.is_valid(raise_exception=True)

        return many_serializer

    @classmethod
    def create_doctask_group(cls,
                             json_content: list[TaskJSON],
                             *args, **kwargs) -> tuple[DocTaskSerializer, list[models.DocTask]]:
        """
        Creates an array of :py:class:`django_tasks.models.DocTask` instances for the given array of
        doc-task data.
        Raises a :py:class:`rest_framework.exceptions.ValidationError` on failure.
        """
        many_serializer = cls.get_task_group_serializer(json_content, *args, **kwargs)
        doctasks = many_serializer.save()

        return many_serializer, doctasks

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """
        Performs the validation of the task coroutine function of the specified
        :py:class:`django_tasks.models.RegisteredTask` with the given input parameters.
        Raises a :py:class:`rest_framework.exceptions.ValidationError` on failure.
        """
        self.context['task_coro'] = get_task_coro(str(attrs['registered_task']), attrs['inputs'])

        return attrs

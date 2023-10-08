from typing import Any

from rest_framework import serializers

from django_tasks import models

from django_tasks.task_inspector import get_coro_info


class DocTaskSerializer(serializers.ModelSerializer):
    registered_task = serializers.SlugRelatedField(
        slug_field='dotted_path', queryset=models.RegisteredTask.objects.all())

    class Meta:
        model = models.DocTask
        read_only_fields = ('id', 'scheduled_at', 'completed_at', 'document')
        fields = ('registered_task', 'inputs', *read_only_fields)

    @classmethod
    def get_task_group_serializer(cls, json_content, *args, **kwargs):
        kwargs.update(dict(many=True, data=json_content))
        many_serializer = cls(*args, **kwargs)
        many_serializer.is_valid(raise_exception=True)

        return many_serializer

    @classmethod
    def create_doctask_group(cls, json_content, *args, **kwargs):
        many_serializer = cls.get_task_group_serializer(json_content, *args, **kwargs)
        doctasks = many_serializer.save()

        return many_serializer, doctasks

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        self.context['coro_info'] = get_coro_info(attrs['registered_task'].dotted_path, **attrs['inputs'])

        return attrs

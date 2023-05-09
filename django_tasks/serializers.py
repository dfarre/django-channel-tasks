from asgiref.sync import async_to_sync

from rest_framework import exceptions, serializers

from django_tasks import models, task_inspector


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
        coroutine_info = task_inspector.TaskCoroInfo(attrs['name'])
        self.context['task_callable'] = coroutine_info.coroutine

        if self.context['task_callable'] is None:
            raise exceptions.ValidationError({'name': "No task coroutine found."})

        params = coroutine_info.parameters
        unknown_params = set(attrs['inputs']) - set(params)

        if unknown_params:
            raise exceptions.ValidationError({'inputs': f'Unknown parameters {unknown_params}.'})

        # TODO: Check required parameters
        return attrs

    def create(self, validated_data):
        return async_to_sync(self.schedule_task)(validated_data)

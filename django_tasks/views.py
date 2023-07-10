from asgiref.sync import async_to_sync

from rest_framework import decorators, response, status, viewsets

from django_tasks import models, serializers


class TaskViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'delete', 'head', 'options', 'trace']
    queryset = models.DocTask.objects.all()
    serializer_class = serializers.DocTaskSerializer

    @decorators.action(detail=False, methods=['post'])
    def schedule(self, request, *args, **kwargs):
        """DRF action that schedules an array of tasks."""
        many_serializer, _ = async_to_sync(self.schedule_many)(request.data)

        return response.Response(data=many_serializer.data, status=status.HTTP_201_CREATED)

    async def schedule_many(self, json_content):
        """Schedules an array of tasks."""
        many_serializer, doctasks = await self.serializer_class.schedule_doctask_group(
            json_content, context=self.get_serializer_context(),
        )
        return many_serializer, doctasks

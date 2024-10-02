import asyncio

from adrf.viewsets import ModelViewSet as AsyncModelViewSet
from rest_framework import decorators, response, status

from django_tasks import models, serializers
from django_tasks.doctask_scheduler import DocTaskScheduler


class TaskViewSet(AsyncModelViewSet):
    http_method_names = ['get', 'post', 'delete', 'head', 'options', 'trace']
    queryset = models.DocTask.objects.all()
    serializer_class = serializers.DocTaskSerializer

    async def create(self, request, *args, **kwargs):
        drf_response = await super().acreate(request, *args, **kwargs)

        await DocTaskScheduler.schedule_doctask(drf_response.data)

        return drf_response

    @decorators.action(detail=False, methods=['post'])
    async def schedule(self, request, *args, **kwargs):
        """DRF action that schedules an array of tasks."""
        many_serializer, _ = await self.serializer_class.create_doctask_group(
            request.data, context=self.get_serializer_context())
        drf_response = response.Response(data=many_serializer.data, status=status.HTTP_201_CREATED)

        await asyncio.gather(*[DocTaskScheduler.schedule_doctask(data) for data in drf_response.data])

        return drf_response

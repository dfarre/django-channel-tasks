import asyncio

from adrf.viewsets import ModelViewSet as AsyncModelViewSet
from rest_framework import decorators, response, status, viewsets

from django_tasks import models, serializers
from django_tasks.doctask_scheduler import DocTaskScheduler
from django_tasks.websocket_client import LocalWebSocketClient


class WSTaskViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'delete', 'head', 'options', 'trace']
    queryset = models.DocTask.objects.all()
    serializer_class = serializers.DocTaskSerializer
    ws_client = LocalWebSocketClient(timeout=300)

    @staticmethod
    def extract_ws_content(*response_data):
        return [{k: data[k] for k in ('registered_task', 'inputs')} for data in response_data]

    def create(self, request, *args, **kwargs):
        drf_response = super().create(request, *args, **kwargs)
        ws_response = self.ws_client.send_locally({'type': 'task.schedule',
                                                   'content': self.extract_ws_content(drf_response.data)})
        return drf_response

    @decorators.action(detail=False, methods=['post'])
    def schedule(self, request, *args, **kwargs):
        """DRF action that schedules an array of tasks through local Websocket."""
        many_serializer, _ = self.serializer_class.create_doctask_group(
            request.data, context=self.get_serializer_context())
        drf_response = response.Response(data=many_serializer.data, status=status.HTTP_201_CREATED)
        ws_response = self.ws_client.send_locally({'type': 'task.schedule',
                                                   'content': self.extract_ws_content(*drf_response.data)})
        return drf_response


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
        """Async DRF action that schedules an array of tasks."""
        many_serializer, _ = await self.serializer_class.create_doctask_group(
            request.data, context=self.get_serializer_context())
        drf_response = response.Response(data=many_serializer.data, status=status.HTTP_201_CREATED)

        await asyncio.gather(*[DocTaskScheduler.schedule_doctask(data) for data in drf_response.data])

        return drf_response

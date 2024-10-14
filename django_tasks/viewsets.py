import asyncio
import json

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

    def create(self, request, *args, **kwargs):
        ws_response = self.ws_client.send_locally({'type': 'task.store', 'content': [request.data]})

        if 'task.badrequest' in ws_response:
            return response.Response(data=json.loads(ws_response), status=status.HTTP_400_BAD_REQUEST)

        return response.Response(status=status.HTTP_201_CREATED)

    @decorators.action(detail=False, methods=['post'])
    def schedule(self, request, *args, **kwargs):
        """DRF action that schedules an array of tasks through local Websocket."""
        ws_response = self.ws_client.send_locally({'type': 'task.store', 'content': request.data})

        if 'task.badrequest' in ws_response:
            return response.Response(data=json.loads(ws_response), status=status.HTTP_400_BAD_REQUEST)

        return response.Response(status=status.HTTP_201_CREATED)


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
        many_serializer, _ = self.serializer_class.create_doctask_group(
            request.data, context=self.get_serializer_context())
        drf_response = response.Response(data=many_serializer.data, status=status.HTTP_201_CREATED)

        await DocTaskScheduler.schedule_doctasks(*drf_response.data)

        return drf_response

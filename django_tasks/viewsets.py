from adrf.viewsets import ModelViewSet as AsyncModelViewSet
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED

from django_tasks import models, serializers
from django_tasks.doctask_scheduler import DocTaskScheduler
from django_tasks.websocket.backend_client import BackendWebSocketClient


class WSTaskViewSet(ModelViewSet):
    http_method_names = ['post', 'delete', 'head', 'options', 'trace']
    queryset = models.DocTask.objects.all()
    serializer_class = serializers.DocTaskSerializer
    ws_client = BackendWebSocketClient()
    auth_header = 'Authorization'

    def create(self, request, *args, **kwargs):
        """DRF action that schedules a doc-task through local Websocket."""
        ws_response = self.ws_client.perform_request('schedule_doctasks', [request.data], headers={
            self.auth_header: request.headers[self.auth_header],
        })
        status = ws_response.pop('http_status')
        return Response(status=HTTP_201_CREATED if status == HTTP_200_OK else status, data=ws_response)

    @action(detail=False, methods=['post'])
    def schedule(self, request, *args, **kwargs):
        """DRF action that schedules an array of doc-tasks through local Websocket."""
        ws_response = self.ws_client.perform_request('schedule_doctasks', request.data, headers={
            self.auth_header: request.headers[self.auth_header],
        })
        status = ws_response.pop('http_status')
        return Response(status=HTTP_201_CREATED if status == HTTP_200_OK else status, data=ws_response)


class TaskViewSet(AsyncModelViewSet):
    http_method_names = ['get', 'head', 'options', 'trace']
    queryset = models.DocTask.objects.all()
    serializer_class = serializers.DocTaskSerializer

    async def create(self, request, *args, **kwargs):  # NO COVER
        drf_response = await super().acreate(request, *args, **kwargs)

        await DocTaskScheduler.schedule_doctask(drf_response.data)

        return drf_response

    @action(detail=False, methods=['post'])
    async def schedule(self, request, *args, **kwargs):  # NO COVER
        """Async DRF action that schedules an array of tasks."""
        many_serializer, _ = self.serializer_class.create_doctask_group(
            request.data, context=self.get_serializer_context())
        drf_response = Response(data=many_serializer.data, status=HTTP_201_CREATED)

        await DocTaskScheduler.schedule_doctasks(*drf_response.data)

        return drf_response

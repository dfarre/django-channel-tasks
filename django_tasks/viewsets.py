"""This module provides the DRF view sets, which are employed in ASGI and WSGI endpoints."""
from adrf.viewsets import ModelViewSet as AsyncModelViewSet
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED

from django_tasks import models, serializers
from django_tasks.scheduler import DocTaskScheduler
from django_tasks.websocket.backend_client import BackendWebSocketClient


class WSTaskViewSet(ModelViewSet):
    """DRF model viewset for :py:class:`django_tasks.models.DocTask`.

    This is currently implemented for running, from a `sync` context, operations that imply modifying the database
    from an `async` context; this class implements sync views that act as a proxy between WSGI and ASGI applications
    within the backend.
    """
    http_method_names = ['post', 'delete', 'head', 'options', 'trace']
    queryset = models.DocTask.objects.all()
    serializer_class = serializers.DocTaskSerializer

    #: Name of the header to include to authorize against the ASGI application.
    auth_header = 'Authorization'

    #: The :py:class:`django_tasks.websocket.backend_client.BackendWebSocketClient` instance employed by this class.
    ws_client = BackendWebSocketClient()

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
    """Asynchronous DRF model viewset for :py:class:`django_tasks.models.DocTask`.

    This is currently implemented for fetching operations only.
    """
    http_method_names = ['get', 'head', 'options', 'trace']
    queryset = models.DocTask.objects.all()
    serializer_class = serializers.DocTaskSerializer

    async def create(self, request, *args, **kwargs):  # NO COVER
        """
        Experimental async view for scheduling a single task, not currently implemented since it
        produces blocking behaviour.
        """
        drf_response = await super().acreate(request, *args, **kwargs)

        await DocTaskScheduler.schedule_doctask(drf_response.data)

        return drf_response

    @action(detail=False, methods=['post'])
    async def schedule(self, request, *args, **kwargs):  # NO COVER
        """
        Experimental async DRF action for scheduleing an array of tasks, not currently implemented
        since it produces blocking behaviour.
        """
        many_serializer, _ = self.serializer_class.create_doctask_group(
            request.data, context=self.get_serializer_context())
        drf_response = Response(data=many_serializer.data, status=HTTP_201_CREATED)

        await DocTaskScheduler.schedule_doctasks(*drf_response.data)

        return drf_response

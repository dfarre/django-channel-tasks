"""This module provides the DRF view sets, which are employed in ASGI and WSGI endpoints."""
from adrf.viewsets import ModelViewSet as AsyncModelViewSet
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED

from django_tasks.models import DocTask
from django_tasks.serializers import DocTaskSerializer
from django_tasks.websocket.backend_client import BackendWebSocketClient


class WSDocTaskViewSet(ModelViewSet):
    """
    DRF model viewset for :py:class:`django_tasks.models.DocTask` that connects to the background task ASGI unit
    through web-socket.
    """
    http_method_names = ['post', 'delete', 'head', 'options', 'trace']
    queryset = DocTask.objects.all()
    serializer_class = DocTaskSerializer

    #: Name of the header to include to authorize against the ASGI application.
    auth_header = 'Authorization'

    #: The :py:class:`django_tasks.websocket.backend_client.BackendWebSocketClient` instance employed by this class.
    ws_client = BackendWebSocketClient()

    def create(self, request: Request, *args, **kwargs):
        """DRF action that schedules a doc-task through local Websocket."""
        ws_response = self.ws_client.perform_request('schedule-store', [request.data], headers={
            self.auth_header: request.headers[self.auth_header],
        })
        status = ws_response.pop('http_status')
        return Response(status=HTTP_201_CREATED if status == HTTP_200_OK else status, data=ws_response)

    @action(detail=False, methods=['post'])
    def schedule(self, request: Request, *args, **kwargs):
        """DRF action that schedules an array of doc-tasks through local Websocket."""
        ws_response = self.ws_client.perform_request('schedule-store', request.data, headers={
            self.auth_header: request.headers[self.auth_header],
        })
        status = ws_response.pop('http_status')
        return Response(status=HTTP_201_CREATED if status == HTTP_200_OK else status, data=ws_response)


class DocTaskViewSet(AsyncModelViewSet):
    """Asynchronous DRF model viewset for :py:class:`django_tasks.models.DocTask`.

    This is currently implemented for fetching operations only.
    """
    http_method_names = ['get', 'head', 'options', 'trace']
    queryset = DocTask.objects.all()
    serializer_class = DocTaskSerializer

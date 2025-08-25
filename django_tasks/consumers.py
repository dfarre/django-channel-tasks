"""
This module defines the consumer classes for background task management.
"""
import abc
import json
import logging
import uuid

from asgiref.sync import sync_to_async

from channels.exceptions import StopConsumer
from channels.consumer import AsyncConsumer
from channels.generic.http import AsyncHttpConsumer
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.conf import settings
from rest_framework import status
from rest_framework.exceptions import ValidationError

from django_tasks.serializers import DocTaskSerializer
from django_tasks.scheduler import DocTaskScheduler, schedule_tasks
from django_tasks.task_cache import TaskCache
from django_tasks.websocket.close_codes import WSCloseCode

from django_tasks.typing import JSON, EventJSON, DocTaskJSON, TaskJSON, WSResponseJSON


class TaskGroupConsumer(AsyncConsumer):
    @property
    def user_group(self) -> str:
        """The name of the group of consumers that is assigned to the user."""
        return f"{self.scope['user'].username}_{settings.CHANNEL_TASKS.channel_group}"

    @property
    def request_id(self) -> str:
        """
        The request ID provided in the corresponding header, or a newly generated ID if the header is missing.
        This value will be returned to clients as an identifier of the request; websocket clients must provide
        it in the Request-ID header in order to be able to check the returned ID value in subsequent messages.
        """
        for name, value in self.scope.get('headers', []):
            if name == b'request-id':
                id_value: str = value.decode()
                return id_value

        return uuid.uuid4().hex


class TaskGroupJsonConsumer(TaskGroupConsumer, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    async def receive_json(self, request_content: JSON) -> int:
        """Process the received, already parsed, JSON request content, and return an HTTP status code."""

    @abc.abstractmethod
    async def send_bad_request_response(self, error: ValidationError) -> None:
        """Send a 400 message in case of validation error."""


class HttpConsumer(AsyncHttpConsumer):
    async def handle(self, body: bytes):
        handler = getattr(self, 'handle_' + self.scope['method'].lower(), None)

        if handler is None:
            await self.send_response(status.HTTP_405_METHOD_NOT_ALLOWED, body=b'')
        else:
            await handler(body)


class TaskScheduleConsumer(TaskGroupJsonConsumer):
    async def receive_json(self, request_content: JSON) -> int:
        """Processes task schedule websocket requests."""
        logging.getLogger('django').debug(
            'Processing task schedule through channel %s. Data: %s', self.channel_name, request_content)
        try:
            many_serializer = await DocTaskSerializer.get_valid_task_group_serializer(request_content)
        except ValidationError as error:
            await self.send_bad_request_response(error)
            return status.HTTP_400_BAD_REQUEST
        else:
            data: list[TaskJSON] = await many_serializer.adata
            await schedule_tasks(self.request_id, self.scope['user'].username, *data)
            return status.HTTP_200_OK


class DocTaskScheduleConsumer(TaskGroupJsonConsumer):
    async def receive_json(self, request_content: JSON) -> int:
        """Processes doc-task schedule websocket requests."""
        logging.getLogger('django').debug(
            'Processing DocTask schedule through channel %s. Data: %s', self.channel_name, request_content)
        try:
            many_serializer, doctasks = await DocTaskSerializer.create_doctask_group(request_content)
        except ValidationError as error:
            await self.send_bad_request_response(error)
            return status.HTTP_400_BAD_REQUEST
        else:
            data: list[DocTaskJSON] = await many_serializer.adata
            await DocTaskScheduler.schedule_doctasks(self.request_id, self.scope['user'].username, *data)
            return status.HTTP_201_CREATED


class TaskCacheClearConsumer(TaskGroupJsonConsumer):
    async def receive_json(self, request_content: JSON) -> int:
        """Clears a specific task cache."""
        logging.getLogger('django').debug(
            'Processing cache clear through channel %s. Data: %s', self.channel_name, request_content)
        await sync_to_async(self.user_task_cache.clear_task_cache)(request_content['task_id'])
        return status.HTTP_200_OK


class TaskWebSocketConsumer(TaskGroupJsonConsumer, AsyncJsonWebsocketConsumer):
    async def send_bad_request_response(self, error: ValidationError) -> None:
        """Broadcasts an HTTP 400 message through the user's group of consumers."""
        content: WSResponseJSON = {
            'http_status': status.HTTP_400_BAD_REQUEST,
            'request_id': self.request_id,
            'details': error.get_full_details(),
        }
        await self.group_send({'type': 'task.badrequest', 'content': content})

    async def group_send(self, event: EventJSON) -> None:
        """Distributes the given `event` through the group of the user of this instance."""
        await self.channel_layer.group_send(self.user_group, event)

    async def task_started(self, event: EventJSON) -> None:
        """Echoes the task.started document."""
        await self.send_json(content=event)

    async def task_success(self, event: EventJSON) -> None:
        """Echoes the task.success document."""
        await self.send_json(content=event)

    async def task_cancelled(self, event: EventJSON) -> None:
        """Echoes the task.cancelled document."""
        await self.send_json(content=event)

    async def task_error(self, event: EventJSON) -> None:
        """Echoes the task.error document."""
        await self.send_json(content=event)

    async def task_badrequest(self, event: EventJSON) -> None:
        """Echoes the task.badrequest document."""
        await self.send_json(content=event)

    async def stop_unauthorized(self) -> None:
        """Stops the consumer if the user is not authenticated."""
        if not self.scope['user'].is_authenticated:
            logging.getLogger('django').warning('Unauthenticated user %s. Closing websocket.', self.scope['user'])
            await self.close(code=WSCloseCode.UNAUTHORIZED)
            raise StopConsumer()

    async def connect(self) -> None:
        """Performs authentication and set-up actions on connection."""
        await self.stop_unauthorized()
        await super().connect()
        self.user_task_cache = TaskCache(self.scope['user'].username)
        await self.channel_layer.group_add(self.user_group, self.channel_name)
        logging.getLogger('django').debug(
            'Connected user "%s" through channel %s.', self.scope['user'].username, self.channel_name)

    async def disconnect(self, close_code: int) -> None:
        """Performs clean-up actions on disconnection."""
        await self.channel_layer.group_discard(self.user_group, self.channel_name)
        logging.getLogger('django').debug(
            'Disconnected channel %s. User: %s. Reason: %s',
            self.channel_name, self.scope['user'].username, repr(WSCloseCode(close_code)))


class TaskScheduleWebSocketConsumer(TaskScheduleConsumer, TaskWebSocketConsumer):
    """The websocket consumer for task schedule requests."""


class DocTaskScheduleWebSocketConsumer(DocTaskScheduleConsumer, TaskWebSocketConsumer):
    """The websocket consumer for doc-task schedule requests."""


class CacheClearWebSocketConsumer(TaskCacheClearConsumer, TaskWebSocketConsumer):
    """The websocket consumer for cache-clear requests."""


class TaskJsonHttpConsumer(TaskGroupJsonConsumer, HttpConsumer):
    async def handle_post(self, body: bytes):
        try:
            request_content: JSON = json.loads(body)
        except json.JSONDecodeError as error:
            await self.send_bad_request_response(ValidationError({'non_field_errors': repr(error)}))
        else:
            http_status = await self.receive_json(request_content)
            if http_status < 400:
                content: WSResponseJSON = {'request_id': self.request_id}
                await self.send_json_response(http_status, content)

    async def send_bad_request_response(self, error: ValidationError) -> None:
        """Broadcasts an HTTP 400 message through the user's group of consumers."""
        content: WSResponseJSON = {
            'request_id': self.request_id, 'details': error.get_full_details(),
        }
        await self.send_json_response(status.HTTP_400_BAD_REQUEST, content)

    async def send_json_response(self, status_code: int, content: WSResponseJSON) -> None:
        await self.send_response(status_code, json.dumps(content).encode(),
                                 headers={b'Content-Type': b'application/json'})


class TaskScheduleHttpConsumer(TaskScheduleConsumer, TaskJsonHttpConsumer):
    """The HTTP consumer for task schedule requests."""


class DocTaskScheduleHttpConsumer(DocTaskScheduleConsumer, TaskJsonHttpConsumer):
    """The HTTP consumer for doc-task schedule requests."""

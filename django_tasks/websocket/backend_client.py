"""
This module provides the :py:class:`django_tasks.websocket.backend_client.BackendWebSocketClient` class,
which manages communications between WSGI and ASGI systems.
"""
from __future__ import annotations
from typing import Any, Callable, Optional

import functools
import json
import logging
import uuid

import websocket

from rest_framework import status
from django.conf import settings

from django_tasks.typing import JSON, WSResponseJSON
from django_tasks.websocket.close_codes import WSCloseCode


def catch_websocket_errors(client_method: Callable) -> Callable:
    """
    Method decorator for :py:class:`django_tasks.websocket.backend_client.BackendWebSocketClient`.
    Decorated methods will catch any :py:class:`websocket.WebSocketException` and return it instead of raising.
    """
    @functools.wraps(client_method)
    def safe_client_method(client: BackendWebSocketClient, *args, **kwargs) -> tuple[bool, Any]:
        try:
            return_value = client_method(client, *args, **kwargs)
            return True, return_value
        except websocket.WebSocketException as error:
            return False, error

    return safe_client_method


class BackendWebSocketClient:
    """
    Wrapper for handy usage of :py:class:`websocket.WebSocket` within the backend, able to handle WSGI requests
    asyncronously through websocket, returning the first websocket messages received from the ASGI endpoint for a
    specific request.
    """
    #: URL path for local access to the ASGI endpoint
    local_route: str = (
        'tasks' if not settings.CHANNEL_TASKS.proxy_route else f'{settings.CHANNEL_TASKS.proxy_route}-local/tasks')

    #: The configured URL for local access to the ASGI endpoint.
    local_url: str = f'ws://127.0.0.1:{settings.CHANNEL_TASKS.local_port}/{local_route}/'

    #: Default headers for the ASGI endpoint.
    default_headers: dict[str, str] = {'Content-Type': 'application/json'}

    #: Default websocket timeout, in seconds. It should be as less as possible for quick responses, since
    #: the client will wait this time for new messages.
    default_timeout: float = 0.1

    #: Maximum number of response messages to collect for a request.
    max_response_msg_collect: int = 2

    def __init__(self, **connect_kwargs):
        self.connect_kwargs = connect_kwargs
        self.connect_kwargs.setdefault('timeout', self.default_timeout)
        self.ws = websocket.WebSocket()
        websocket.setdefaulttimeout(self.connect_kwargs['timeout'])

    def __repr__(self):
        return f'<BackendWebSocketClient: {self.connect_kwargs}>'

    def perform_request(self,
                        action: str,
                        content: JSON,
                        headers: Optional[dict[str, str]] = None) -> WSResponseJSON:
        header = headers or {}
        header.update(self.default_headers)
        header['Request-ID'] = uuid.uuid4().hex

        connect_ok, connect_error = self.connect(action, header)
        if not connect_ok:
            return self.bad_gateway_message(header['Request-ID'], connect_error)

        send_ok, send_error = self.send_json(content)
        if not send_ok:
            return self.bad_gateway_message(header['Request-ID'], send_error)

        response = self.get_first_response(header['Request-ID'])
        self.disconnect(
            WSCloseCode.BAD_GATEWAY if response['http_status'] == status.HTTP_502_BAD_GATEWAY
            else WSCloseCode.NORMAL)

        return response

    @staticmethod
    def bad_gateway_message(request_id: str, error: websocket.WebSocketException) -> WSResponseJSON:
        """Constructs and returns the bad gateway message.

        :param request_id: The universal ID of the request that raised the error.
        :param error: The web-socket error raised during the request.
        """
        return {
            'request_id': request_id,
            'http_status': status.HTTP_502_BAD_GATEWAY,
            'details': [repr(error)],
        }

    @catch_websocket_errors
    def connect(self, action: str, header: dict[str, str]):
        """Tries to connect to the corresponding endpoint with the given headers."""
        return self.ws.connect(self.local_url + action, header=header, **self.connect_kwargs)

    @catch_websocket_errors
    def disconnect(self, close_code: int):
        """Tries to disconnect with the given close code."""
        return self.ws.close(status=close_code)

    @catch_websocket_errors
    def send_json(self, json_data: JSON):
        """Tries to send the given JSON data."""
        return self.ws.send(json.dumps(json_data))

    @catch_websocket_errors
    def receive(self):
        """Tries to receive a message."""
        return self.ws.recv()

    def get_first_response(self, request_id: str) -> WSResponseJSON:
        """
        Having performed a request with the given ID, collects and returns the first response messages
        to that request.
        """
        response: WSResponseJSON = {
            'request_id': request_id, 'details': [], 'http_status': status.HTTP_502_BAD_GATEWAY
        }
        http_statuses: list[int] = []

        for _ in range(self.max_response_msg_collect):
            ok, raw_msg = self.receive()

            if not ok or not raw_msg:
                break

            is_response: bool = True
            try:
                msg = json.loads(raw_msg)
            except json.JSONDecodeError:
                is_response = False
            else:
                if msg.get('content', {}).get('request_id') == request_id:
                    bad_request_response: WSResponseJSON = msg['content']
                    return bad_request_response
                elif msg.get('content', {}).get('task_id'):
                    task_request_id, _ = msg['content']['task_id'].split('.')
                    if task_request_id == request_id:
                        logging.getLogger('django').debug(
                            'Received response message to request %s: %s', request_id, msg)
                        http_statuses.append(msg['content']['detail'].pop('http_status'))
                        response['details'].append(msg['content']['detail'])
                    else:
                        is_response = False
                else:
                    is_response = False

            if is_response is False:
                logging.getLogger('django').debug(
                    'Discarded unrelated message, received after request %s: %s', request_id, raw_msg)

        if http_statuses:
            response['http_status'] = max(http_statuses)

        return response

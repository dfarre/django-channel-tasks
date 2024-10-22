import functools
import json
import logging
import uuid
import websocket

from typing import Optional, Any

from rest_framework import status
from django.conf import settings

from django_tasks.websocket import close_codes


def catch_websocket_errors(client_method):
    @functools.wraps(client_method)
    def safe_client_method(client, *args, **kwargs) -> tuple[bool, Any]:
        try:
            return_value = client_method(client, *args, **kwargs)
            return True, return_value
        except websocket.WebSocketException as error:
            return False, error

    return safe_client_method


class BackendWebSocketClient:
    """Wrapper for handy usage of `websocket.WebSocket` within the backend, able to:
      * Handle WSGI requests asyncronously through websocket, returning the first websocket message
        received for a specific request.
    """
    local_route = ('tasks' if not settings.CHANNEL_TASKS.proxy_route
                   else f'{settings.CHANNEL_TASKS.proxy_route}-local/tasks')
    local_url = f'ws://127.0.0.1:{settings.CHANNEL_TASKS.local_port}/{local_route}/'
    headers = {'Content-Type': 'application/json'}
    max_response_msg_collect = 2
    default_timeout = 0.1

    def __init__(self, **connect_kwargs):
        self.connect_kwargs = connect_kwargs
        self.connect_kwargs.setdefault('timeout', self.default_timeout)
        self.ws = websocket.WebSocket()
        websocket.setdefaulttimeout(self.connect_kwargs['timeout'])

    def perform_request(self, action: str, content: dict, headers: Optional[dict] = None) -> dict:
        header = headers or {}
        header.update(self.headers)
        header['Request-ID'] = uuid.uuid4().hex

        connect_ok, connect_error = self.connect(header)
        if not connect_ok:
            return self.bad_gateway_message(header['Request-ID'], connect_error)

        send_ok, send_error = self.send_json(dict(action=action, content=content))
        if not send_ok:
            return self.bad_gateway_message(header['Request-ID'], send_error)

        response = self.get_first_response(header['Request-ID'])
        self.disconnect(
            close_codes.BAD_GATEWAY if response['http_status'] == status.HTTP_502_BAD_GATEWAY
            else close_codes.OK)

        return response

    @staticmethod
    def bad_gateway_message(request_id: str, error: websocket.WebSocketException):
        return {'http_status': status.HTTP_502_BAD_GATEWAY,
                'request_id': request_id,
                'details': repr(error)}

    @catch_websocket_errors
    def connect(self, header: dict):
        return self.ws.connect(self.local_url, header=header, **self.connect_kwargs)

    @catch_websocket_errors
    def disconnect(self, close_code: int):
        return self.ws.close(status=close_code)

    @catch_websocket_errors
    def send_json(self, json_data):
        return self.ws.send(json.dumps(json_data))

    @catch_websocket_errors
    def receive(self):
        return self.ws.recv()

    def get_first_response(self, request_id: str):
        response = {'request_id': request_id, 'first_messages': []}
        http_statuses = []

        for _ in range(self.max_response_msg_collect):
            ok, raw_msg = self.receive()

            if not ok or not raw_msg:
                break

            is_response = True
            try:
                msg = json.loads(raw_msg)
            except json.JSONDecodeError:
                is_response = False
            else:
                task_id = msg.get('content', {}).pop('task_id', '').split('.')
                reqid = msg.get('content', {}).pop('request_id', '')

                if len(task_id) == 2 and task_id[0] == request_id or reqid and reqid == request_id:
                    logging.getLogger('django').debug('Received response message to request %s: %s', request_id, msg)
                else:
                    is_response = False

            if is_response:
                http_statuses.append(msg['content']['http_status'])
                response['first_messages'].append(msg['content'])
            else:
                logging.getLogger('django').debug(
                    'Discarded unknown message, received after request %s: %s', request_id, raw_msg)

        response['http_status'] = max(http_statuses) if http_statuses else status.HTTP_502_BAD_GATEWAY

        return response

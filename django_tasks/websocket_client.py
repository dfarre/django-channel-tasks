from asgiref.sync import sync_to_async

import uuid

import asyncio
import collections
import json
import logging
import websocket

from rest_framework import status
from django.conf import settings


class LocalWebSocketClient:
    """Wrapper for handy usage of `websocket.WebSocket` within the backend, able to:
      * Handle WSGI requests asyncronously through websocket, returning the first websocket message
        received for a specific request.
    """
    local_route = ('tasks' if not settings.CHANNEL_TASKS.proxy_route
                   else f'{settings.CHANNEL_TASKS.proxy_route}-local/tasks')
    local_url = f'ws://127.0.0.1:{settings.CHANNEL_TASKS.local_port}/{local_route}/'
    header = {'Content-Type': 'application/json'}
    max_response_msg_count = 10

    def __init__(self, **connect_kwargs):
        self.connect_kwargs = connect_kwargs
        self.ws = websocket.WebSocket()
        websocket.setdefaulttimeout(self.connect_kwargs.get('timeout', 10))

    def perform_request(self, action: str, content: dict):
        self.ws.connect(self.local_url, header=self.header, **self.connect_kwargs)
        event = dict(request_id=uuid.uuid4().hex, action=action, content=content)
        self.ws.send(json.dumps(event))
        first_response = self.get_first_response(event['request_id'])
        self.ws.close()

        return first_response

    def get_first_response(self, request_id: str):
        for i in range(self.max_response_msg_count):
            raw_msg = self.ws.recv()
            is_response = True

            try:
                msg = json.loads(raw_msg)
            except json.JSONDecodeError as error:
                is_response = False
            else:
                if msg.get('request_id') == request_id:
                    logging.getLogger('django').debug('Received first response to request %s: %s', request_id, msg)
                else:
                    is_response = False

            if is_response:
                return msg
            else:
                logging.getLogger('django').warning('Unknown message received after request %s: %s', request_id, msg)

        return {'http_status': status.HTTP_502_BAD_GATEWAY, 'request_id': request_id, 'details': 'No response.'}

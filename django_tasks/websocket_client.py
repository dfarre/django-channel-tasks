from asgiref.sync import sync_to_async

import uuid

import asyncio
import collections
import json
import logging
import websocket

from typing import Optional

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
    headers = {'Content-Type': 'application/json'}
    max_unknown_msg_count = 4
    max_response_msg_collect = 1


    def __init__(self, **connect_kwargs):
        self.connect_kwargs = connect_kwargs
        self.ws = websocket.WebSocket()
        websocket.setdefaulttimeout(self.connect_kwargs.get('timeout', 10))

    def perform_request(self, action: str, content: dict, headers: Optional[dict]=None) -> dict:
        header = headers or {}
        header.update(self.headers)
        header['Request-ID'] = uuid.uuid4().hex

        try:
            self.ws.connect(self.local_url, header=header, **self.connect_kwargs)
            self.ws.send(json.dumps(dict(action=action, content=content)))
            response = self.get_first_response(header['Request-ID'])
        except Exception as exc:
             return {'http_status': status.HTTP_502_BAD_GATEWAY,
                     'request_id': header['Request-ID'],
                     'details': repr(exc)}
        else:
            self.ws.close()
            return response

    def get_first_response(self, request_id: str):
        msgs_key = f'first{self.max_response_msg_collect}messages'
        response = {'request_id': request_id, msgs_key: []}
        http_statuses = []

        for i in range(self.max_response_msg_collect + self.max_unknown_msg_count):
            raw_msg = self.ws.recv()
            is_response = True

            try:
                msg = json.loads(raw_msg)
            except json.JSONDecodeError as error:
                is_response = False
            else:
                if msg.get('content', {}).pop('request_id', None) == request_id:
                    logging.getLogger('django').debug('Received response message to request %s: %s', request_id, msg)
                else:
                    is_response = False

            if is_response:
                http_statuses.append(msg['content']['http_status'])
                response[msgs_key].append(msg['content'])

                if len(response[msgs_key]) == self.max_response_msg_collect:
                    break
                else:
                    continue
            else:
                logging.getLogger('django').warning('Unknown message received after request %s: %s', request_id, raw_msg)

        response['http_status'] = max(http_statuses) if http_statuses else status.HTTP_502_BAD_GATEWAY

        return response

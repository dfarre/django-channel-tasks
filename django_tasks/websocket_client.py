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
    """Wrapper for handy usage of `websocket.WebSocket` within localhost."""
    local_route = ('tasks' if not settings.CHANNEL_TASKS.proxy_route
                   else f'{settings.CHANNEL_TASKS.proxy_route}-local/tasks')
    local_url = f'ws://127.0.0.1:{settings.CHANNEL_TASKS.local_port}/{local_route}/'
    header = {'Content-Type': 'application/json'}

    def __init__(self, **connect_kwargs):
        self.connect_kwargs = connect_kwargs
        self.ws = websocket.WebSocket()
        self.events = collections.defaultdict(list)
        websocket.setdefaulttimeout(self.connect_kwargs.get('timeout', 10))
        self.wsapp = websocket.WebSocketApp(
            self.local_url, header=self.header, on_message=self.on_message, on_error=self.on_error,
        )
        self.expected_events = {}

    def perform_request(self, action: str, content: dict):
        self.ws.connect(self.local_url, header=self.header, **self.connect_kwargs)
        event = dict(request_id=uuid.uuid4().hex, action=action, content=content)
        self.ws.send(json.dumps(event))
        first_response = self.get_first_response(event['request_id'])
        self.ws.close()

        return first_response

    def get_first_response(self, request_id: str):
        msg = json.loads(self.ws.recv())
        logging.getLogger('django').debug('First local WS message: %s. RequestID: %s', msg, request_id)

        if msg.get('request_id') == request_id:
            return msg

        return {'http_status': status.HTTP_502_BAD_GATEWAY, 'request_id': request_id, 'details': 'No response.'}

    def on_message(self, wsapp, message: str):
        logging.getLogger('django').debug('Received local WS message: %s', message)
        # event = json.loads(message)
        # self.events[event['content']['status'].lower()].append(event)

        # if self.expected_events and self.expected_events_collected:
        #     wsapp.close()

    def on_error(self, wsapp, error: websocket.WebSocketTimeoutException):
        logging.getLogger('django').error('Catched local WS error: %s. Closing connection.', error)
        wsapp.close()

    def collect_events(self, event_loop):
        return asyncio.wrap_future(asyncio.run_coroutine_threadsafe(
            sync_to_async(self.wsapp.run_forever)(), event_loop))

    @property
    def expected_events_collected(self) -> bool:
        return all(len(self.events[event_type]) == count
                   for event_type, count in self.expected_events.items())

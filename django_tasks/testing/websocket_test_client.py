from asgiref.sync import sync_to_async

import asyncio
import collections
import json
import logging
import websocket

from django.conf import settings


class TestingWebSocketClient:
    """Wrapper for handy usage of `websocket.WebSocketApp` for testing."""
    local_route = ('tasks' if not settings.CHANNEL_TASKS.proxy_route
                   else f'{settings.CHANNEL_TASKS.proxy_route}-local/tasks')
    local_url = f'ws://127.0.0.1:{settings.CHANNEL_TASKS.local_port}/{local_route}/clear-cache'
    header = {'Content-Type': 'application/json'}

    def __init__(self, timeout=8):
        websocket.setdefaulttimeout(timeout)
        self.wsapp = websocket.WebSocketApp(
            self.local_url, header=self.header, on_message=self.on_message, on_error=self.on_error,
        )
        self.events = collections.defaultdict(list)
        self.expected_events = {}

    def on_message(self, wsapp, message: str):
        logging.getLogger('django').debug('Received local WS message: %s', message)
        task_event = json.loads(message)
        self.events[task_event['status'].lower()].append(task_event)

        if self.expected_events and self.expected_events_collected:
            wsapp.close()

    def on_error(self, wsapp, error: websocket.WebSocketTimeoutException):
        logging.getLogger('django').error('Catched local WS error: %s. Closing connection.', error)
        wsapp.close()

    def collect_events(self, event_loop):
        return asyncio.wrap_future(asyncio.run_coroutine_threadsafe(
            sync_to_async(self.wsapp.run_forever)(), event_loop))

    @property
    def expected_events_collected(self) -> bool:
        return all(len(self.events[event_type]) == count for event_type, count in self.expected_events.items())

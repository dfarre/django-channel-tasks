import json
import os
import ssl

import websocket

from django.conf import settings
from django.http import HttpRequest


class WebsocketClientWrapper:
    default_headers: dict[str, str] = {'Content-Type': 'application/json'}

    def __init__(self, timeout: float = 90, **headers):
        self.timeout = timeout
        self.headers = {**self.default_headers, **headers}
        self.client = websocket.WebSocket(sslopt={'cert_reqs': ssl.CERT_NONE})

    def schedule_task(self, http_request: HttpRequest, task_name: str, **inputs):
        secure = 's' if http_request.is_secure() else ''
        origin = f'http{secure}://{http_request.get_host()}'
        address = os.path.join(
            http_request.get_host(), settings.CHANNEL_TASKS.proxy_route, 'tasks')
        self.client.connect(
            f'ws{secure}://{address}/', header=self.headers, timeout=self.timeout,
            origin=origin, cookie=http_request.headers.get('Cookie'),
        )
        self.client.send(json.dumps([dict(name=task_name, inputs=inputs)], indent=4))

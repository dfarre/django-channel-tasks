import json
import os

import websocket

from django.conf import settings
from django.http import HttpRequest


class WebsocketClientWrapper:
    default_headers: dict[str, str] = {'Content-Type': 'application/json'}

    def __init__(self, timeout: float = 90, certs_base_dir: str = '/etc/letsencrypt/live'):
        self.timeout = timeout
        self.certs_base_dir = certs_base_dir

    @property
    def certs_dir(self):
        return f'{self.certs_base_dir}/{settings.CHANNEL_TASKS.server_name}'

    def get_client(self, *, is_secure):
        if not is_secure:
            return websocket.WebSocket()

        return websocket.WebSocket(sslopt={
            'check_hostname': True,
            'certfile': f'{self.certs_dir}/fullchain.pem',
            'keyfile': f'{self.certs_dir}/privkey.pem',
        })

    def schedule_task(self, http_request: HttpRequest, task_name: str, **inputs):
        secure = 's' if http_request.is_secure() else ''
        origin = f'http{secure}://{http_request.get_host()}'
        address = os.path.join(
            http_request.get_host(), settings.CHANNEL_TASKS.proxy_route, 'tasks'
        )
        client = self.get_client(is_secure=secure)
        client.connect(
            f'ws{secure}://{address}/', header=self.default_headers, timeout=self.timeout,
            origin=origin, cookie=http_request.headers.get('Cookie'),
        )
        client.send(json.dumps([dict(name=task_name, inputs=inputs)], indent=4))

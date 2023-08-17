import functools
import json

import websocket

from django.contrib import admin, messages
from django.core.handlers.asgi import ASGIRequest


class AdminTaskAction:
    header = {'Content-Type': 'application/json'}

    def __init__(self, task_name: str, **kwargs):
        self.task_name = task_name
        self.kwargs = kwargs

    def __call__(self, post_schedule_callable):
        @admin.action(**self.kwargs)
        @functools.wraps(post_schedule_callable)
        def action_callable(modeladmin: admin.ModelAdmin, request: ASGIRequest, queryset):
            ws_response = self.websocket_task_schedule(
                request, self.task_name, instance_ids=list(queryset.values_list('pk', flat=True))
            )
            modeladmin.message_user(request, ws_response, messages.INFO)
            return post_schedule_callable(modeladmin, request, queryset)

        return action_callable

    def websocket_task_schedule(self, http_request, task_name, **inputs):
        ws = websocket.WebSocket()
        ws.connect(f'ws://{http_request.get_host()}/tasks/', header=self.header)
        ws.send(json.dumps([dict(name=task_name, inputs=inputs)], indent=4))
        ws_response = ws.recv()
        ws.close()
        return ws_response

import json

import websocket

from django.contrib import admin, messages
from django.core.handlers.asgi import ASGIRequest


class AdminTaskActionFactory:
    header = {'Content-Type': 'application/json'}

    @classmethod
    def new(cls, name, **kwargs):
        @admin.action(**kwargs)
        def action_callable(modeladmin: admin.ModelAdmin, request: ASGIRequest, queryset):
            ws_response = cls.websocket_task_schedule(
                request, name, instance_ids=list(queryset.values_list('pk', flat=True))
            )
            modeladmin.message_user(request, ws_response, messages.INFO)

        action_callable.__name__ = name
        return action_callable

    @classmethod
    def websocket_task_schedule(cls, http_request, task_name, **inputs):
        ws = websocket.WebSocket()
        ws.connect(f'ws://{http_request.get_host()}/tasks/', header=cls.header)
        ws.send(json.dumps([dict(name=task_name, inputs=inputs)], indent=4))
        ws_response = ws.recv()
        ws.close()
        return ws_response

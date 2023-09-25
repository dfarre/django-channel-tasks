import functools
import json
import os

from typing import Any, Callable, Optional

import websocket

from django.conf import settings
from django.contrib import admin, messages
from django.db.models import QuerySet
from django.http import HttpRequest


PROXY_ROUTE = settings.CHANNEL_TASKS.proxy_route


class AdminTaskAction:
    default_headers: dict[str, str] = {'Content-Type': 'application/json'}
    pass_headers: set[str] = {'Cookie'}
    timeout = 8

    def __init__(self, task_name: str, **kwargs):
        self.task_name = task_name
        self.kwargs = kwargs
        self.header = {**self.default_headers}

    def __call__(self, post_schedule_callable: Callable[[Any, HttpRequest, QuerySet], Any]):
        @admin.action(**self.kwargs)
        @functools.wraps(post_schedule_callable)
        def action_callable(modeladmin: admin.ModelAdmin, request: HttpRequest, queryset):
            ws_response = self.websocket_task_schedule(
                request, self.task_name, instance_ids=list(queryset.values_list('pk', flat=True))
            )
            modeladmin.message_user(request, ws_response, messages.INFO)
            return post_schedule_callable(modeladmin, request, queryset)

        return action_callable

    def websocket_task_schedule(self, http_request: HttpRequest, task_name: str, **inputs):
        protocol = 'wss' if http_request.is_secure() else 'ws'
        path = os.path.join(http_request.get_host(), PROXY_ROUTE, 'tasks')
        self.header.update({
            k: http_request.headers[k] for k in self.pass_headers & set(http_request.headers)}
        )
        ws = websocket.WebSocket()
        ws.connect(
            f'{protocol}://{path}/', header=self.header, timeout=self.timeout,
            http_proxy_host=settings.CHANNEL_TASKS.proxy_host,
            http_proxy_port=settings.CHANNEL_TASKS.proxy_port,
            proxy_type=settings.CHANNEL_TASKS.proxy_type,
        )
        ws.send(json.dumps([dict(name=task_name, inputs=inputs)], indent=4))
        response = ws.recv()

        return response


class ExtraContextModelAdmin(admin.ModelAdmin):
    def changelist_view(self, request: HttpRequest, extra_context: Optional[dict] = None):
        extra_context = extra_context or {}
        self.add_changelist_extra_context(request, extra_context)

        return super().changelist_view(request, extra_context=extra_context)

    def add_changelist_extra_context(self, request: HttpRequest, extra_context: dict):
        raise NotImplementedError


class StatusDisplayModelAdmin(ExtraContextModelAdmin):
    change_list_template = 'task_status_display.html'

    def add_changelist_extra_context(self, request: HttpRequest, extra_context: dict):
        extra_context['websocket_uri'] = os.path.join('/', PROXY_ROUTE, 'tasks/')

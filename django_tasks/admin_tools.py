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
    header: dict[str, str] = {'Content-Type': 'application/json'}
    timeout = 20

    def __init__(self, task_name: str, **kwargs):
        self.task_name = task_name
        self.kwargs = kwargs

    def __call__(self, post_schedule_callable: Callable[[Any, HttpRequest, QuerySet], Any]):
        @admin.action(**self.kwargs)
        @functools.wraps(post_schedule_callable)
        def action_callable(modeladmin: admin.ModelAdmin, request: HttpRequest, queryset):
            self.websocket_task_schedule(
                request, self.task_name, instance_ids=list(queryset.values_list('pk', flat=True))
            )
            objects_repr = str(queryset) if queryset.count() > 1 else str(queryset.first())
            modeladmin.message_user(
                request,
                f"Requested to run '{self.task_name}' on {objects_repr}, this page will notify you when done.",
                messages.INFO)
            return post_schedule_callable(modeladmin, request, queryset)

        return action_callable

    def websocket_task_schedule(self, http_request: HttpRequest, task_name: str, **inputs):
        secure = 's' if http_request.is_secure() else ''
        origin = f'http{secure}://{http_request.get_host()}'
        address = os.path.join(http_request.get_host(), PROXY_ROUTE, 'tasks')
        ws = websocket.WebSocket()
        ws.connect(
            f'ws{secure}://{address}/', header=self.header, timeout=self.timeout,
            origin=origin, cookie=http_request.headers.get('Cookie'),
        )
        ws.send(json.dumps([dict(name=task_name, inputs=inputs)], indent=4))


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

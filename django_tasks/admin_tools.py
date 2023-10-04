import functools
import json
import os
import websocket

from typing import Any, Callable, Optional

from django.conf import settings
from django.contrib import admin, messages
from django.db.models import QuerySet
from django.http import HttpRequest


class AdminTaskAction:
    def __init__(self, task_name: str, connect_timeout: float = 90, **kwargs):
        self.task_name = task_name
        self.connect_timeout = connect_timeout
        self.kwargs = kwargs
        self.client = websocket.WebSocket()

    def __call__(self, post_schedule_callable: Callable[[Any, HttpRequest, QuerySet], Any]):
        @admin.action(**self.kwargs)
        @functools.wraps(post_schedule_callable)
        def action_callable(modeladmin: admin.ModelAdmin, request: HttpRequest, queryset):
            local_route = ('tasks' if not settings.CHANNEL_TASKS.proxy_route
                           else f'{settings.CHANNEL_TASKS.proxy_route}-local/tasks')
            self.client.connect(
                f'ws://127.0.0.1:{settings.CHANNEL_TASKS.local_port}/{local_route}/',
                header={'Content-Type': 'application/json'},
                timeout=self.connect_timeout,
            )
            self.client.send(json.dumps([
                dict(name=self.task_name, inputs={'instance_ids': list(queryset.values_list('pk', flat=True))}),
            ]))
            objects_repr = str(queryset) if queryset.count() > 1 else str(queryset.first())
            modeladmin.message_user(
                request,
                f"Requested to run '{self.task_name}' on {objects_repr}, this page will notify you when done.",
                messages.INFO)
            return post_schedule_callable(modeladmin, request, queryset)

        return action_callable


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
        extra_context['websocket_uri'] = os.path.join('/', settings.CHANNEL_TASKS.proxy_route, 'tasks/')

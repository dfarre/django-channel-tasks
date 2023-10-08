import functools
import inspect
import json
import logging
import os
import websocket

from typing import Any, Callable, Optional

from django.conf import settings
from django.contrib import admin, messages
from django.db.models import QuerySet
from django.http import HttpRequest

from django_tasks import models


def register_task(callable: Callable):
    """To be employed as a mark decorator."""
    assert inspect.iscoroutinefunction(callable), 'The function must be a coroutine'

    instance, created = models.RegisteredTask.objects.get_or_create(
        dotted_path=f'{inspect.getmodule(callable).__spec__.name}.{callable.__name__}'
    )
    msg = 'Registered new task %s' if created else 'Task %s already registered'
    logging.getLogger('django').info(msg, instance)

    return callable


class AdminTaskAction:
    def __init__(self, task_name: str, **kwargs):
        self.task_name = task_name
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
                timeout=600,
            )
            self.client.send(json.dumps([
                dict(registered_task=self.task_name,
                     inputs={'instance_ids': list(queryset.values_list('pk', flat=True))}),
            ]))
            objects_repr = str(queryset) if queryset.count() > 1 else str(queryset.first())
            modeladmin.message_user(
                request,
                f"Requested to run '{self.task_name}' on {objects_repr}, this page will notify you of updates.",
                messages.INFO
            )
            ws_response = self.client.recv()
            modeladmin.message_user(request,
                                    f'Received response: {ws_response}',
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

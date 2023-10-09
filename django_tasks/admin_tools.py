import asyncio
import functools
import inspect
import json
import logging
import os
import websocket

from typing import Any, Callable, Optional

from channels.db import database_sync_to_async

from django.conf import settings
from django.contrib import admin, messages
from django.db.models import QuerySet
from django.http import HttpRequest

from django_tasks import models


class ModelTask:
    def __init__(self, model_class, instance_task):
        self.model_class = model_class
        self.instance_task = instance_task

    async def __call__(self, instance_ids):
        logging.getLogger('django').info(
            'Running %s on %s objects %s...',
            self.instance_task.__name__, self.model_class.__name__, instance_ids,
        )
        outputs = await asyncio.gather(*[self.run(pk) for pk in instance_ids])
        return outputs

    async def run(self, instance_id):
        try:
            instance = await self.model_class.objects.aget(pk=instance_id)
        except self.model_class.DoesNotExist:
            logging.getLogger('django').error(
                'Instance of %s with pk=%s not found.', self.model_class.__name__, instance_id)
        else:
            try:
                output = await database_sync_to_async(self.instance_task)(instance)
            except Exception:
                logging.getLogger('django').exception('Got exception:')
            else:
                return output


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
    def __init__(self, task_name: str, socket_timeout: int = 600, **kwargs):
        self.task_name = task_name
        self.socket_timeout = socket_timeout
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
                timeout=self.socket_timeout,
            )
            self.client.send(json.dumps([
                dict(registered_task=self.task_name,
                     inputs={'instance_ids': list(queryset.values_list('pk', flat=True))}),
            ]))
            ws_response = self.client.recv()
            self.client.close()

            objects_repr = str(queryset) if queryset.count() > 1 else str(queryset.first())
            modeladmin.message_user(
                request,
                f"Requested to run '{self.task_name}' on {objects_repr}. Received response: {ws_response}. "
                'This page will notify you of updates.',
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

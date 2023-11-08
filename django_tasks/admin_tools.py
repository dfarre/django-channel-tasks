import asyncio
import functools
import inspect
import logging
import os

from typing import Any, Callable, Optional

from channels.db import database_sync_to_async

from django.apps import apps
from django.conf import settings
from django.contrib import admin, messages
from django.core.cache import cache
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponseRedirect

from django_tasks.websocket_client import LocalWebSocketClient


class ChannelTasksAdminSite(admin.AdminSite):
    def each_context(self, request: HttpRequest):
        context = super().each_context(request)
        context['websocket_uri'] = os.path.join('/', settings.CHANNEL_TASKS.proxy_route, 'tasks/')
        context['cached_task_events'] = cache.get(f'{request.user.username}.task_events', {})
        return context


class ModelTask:
    def __init__(self, app_name: str, model_name: str, instance_task):
        self.model_class = apps.get_model(app_name, model_name)
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
    RegisteredTask = apps.get_model('django_tasks', 'RegisteredTask')
    instance, created = RegisteredTask.objects.get_or_create(
        dotted_path=f'{inspect.getmodule(callable).__spec__.name}.{callable.__name__}'
    )
    msg = 'Registered new task %s' if created else 'Task %s already registered'
    logging.getLogger('django').info(msg, instance)

    return callable


class AdminTaskAction:
    def __init__(self, task_name: str, socket_timeout: int = 600, **kwargs):
        self.task_name = task_name
        self.kwargs = kwargs
        self.client = LocalWebSocketClient(timeout=socket_timeout)

    def __call__(self, post_schedule_callable: Callable[[Any, HttpRequest, QuerySet], Any]):
        @admin.action(**self.kwargs)
        @functools.wraps(post_schedule_callable)
        def action_callable(modeladmin: admin.ModelAdmin, request: HttpRequest, queryset):
            ws_response = self.client.send_locally({
                'type': 'task.schedule',
                'content': [dict(registered_task=self.task_name,
                            inputs={'instance_ids': list(queryset.values_list('pk', flat=True))})],
            })
            objects_repr = str(queryset) if queryset.count() > 1 else str(queryset.first())
            description = self.kwargs.get('description', self.task_name)
            msg = f"Requested to '{description}' on {objects_repr}."
            modeladmin.message_user(request, msg, messages.INFO)

            return post_schedule_callable(modeladmin, request, queryset, ws_response)

        return action_callable


class ExtraContextModelAdmin(admin.ModelAdmin):
    def changelist_view(self, request: HttpRequest, extra_context: Optional[dict] = None):
        extra_context = extra_context or {}
        self.add_changelist_extra_context(request, extra_context)

        return super().changelist_view(request, extra_context=extra_context)

    def add_changelist_extra_context(self, request: HttpRequest, extra_context: dict):
        raise NotImplementedError

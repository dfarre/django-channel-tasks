"""
This module provides the base :py:class:`django.contrib.admin.AdminSite` class featuring background task management,
along with the tools for scheduling tasks as Django Admin actions.
"""
import asyncio
import functools
import logging
import os

from typing import Any, Callable

from channels.db import database_sync_to_async

from django.apps import apps
from django.conf import settings
from django.contrib import admin, messages
from django.db.models import QuerySet
from django.http import HttpRequest

from django_tasks.task_cache import TaskCache
from django_tasks.websocket.backend_client import BackendWebSocketClient
from django_tasks.typing import WSResponseJSON


class ChannelTasksAdminSite(admin.AdminSite):
    """The base admin site class."""
    site_title = 'Django Channel Tasks Admin'
    site_header = 'Channel Tasks'
    index_title = 'Index'

    def each_context(self, request: HttpRequest):
        context = super().each_context(request)
        context['websocket_uri'] = os.path.join('/', settings.CHANNEL_TASKS.proxy_route, 'tasks/')
        context['websocket_port'] = os.getenv('CHANNEL_TASKS_ASGI_PORT', 8001)
        username = getattr(request.user, 'username')
        context['cached_task_events'] = (
            TaskCache(username).get_index() if username and request.user.is_authenticated else {}
        )
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


class AdminTaskAction:
    def __init__(self, task_name: str, **kwargs):
        self.task_name = task_name
        self.kwargs = kwargs
        self.client = BackendWebSocketClient()

    def __call__(self,
                 post_schedule_callable: Callable[[admin.ModelAdmin, HttpRequest, QuerySet, WSResponseJSON], Any]):
        @admin.action(**self.kwargs)
        @functools.wraps(post_schedule_callable)
        def action_callable(modeladmin: admin.ModelAdmin, request: HttpRequest, queryset):
            objects_repr = str(queryset) if queryset.count() > 1 else str(queryset.first())
            ws_response = self.client.perform_request('schedule_tasks', [dict(
                registered_task=self.task_name,
                inputs={'instance_ids': list(queryset.values_list('pk', flat=True))}
            )], headers={'Cookie': request.headers['Cookie']})
            description = self.kwargs.get('description', self.task_name)
            msg = f"Requested to '{description}' on {objects_repr}."
            modeladmin.message_user(request, msg, messages.INFO)

            return post_schedule_callable(modeladmin, request, queryset, ws_response)

        return action_callable

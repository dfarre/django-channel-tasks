"""
This module provides the base :py:class:`django.contrib.admin.AdminSite` class featuring background task management,
along with the tools for scheduling tasks as Django Admin actions.
"""
import abc
import asyncio
import functools
import itertools
import logging
import os

from asgiref.sync import sync_to_async
from typing import Any, Callable

from django.apps import apps
from django.conf import settings
from django.contrib import admin, messages
from django.core import mail
from django.db.models import Model, QuerySet
from django.http import HttpRequest

from django_tasks.task_cache import TaskCache
from django_tasks.websocket.backend_client import BackendWebSocketClient
from django_tasks.typing import WSResponseJSON


ADMIN_LEVEL_NAMES = ['INFO', 'SUCCESS', 'WARNING', 'ERROR']
ADMIN_LEVELS = {getattr(messages, k): k for k in ADMIN_LEVEL_NAMES}


def log_outputs(outputs):
    logger = logging.getLogger('django')

    for output, level in outputs:
        getattr(logger, ADMIN_LEVELS[level].lower(), logger.info)(output)


def get_outputs_summary(*outputs, max_messages=200):
    summary = {level_name: [
        output for output, level in itertools.chain(*outputs) if ADMIN_LEVELS[level] == level_name
    ] for level_name in ADMIN_LEVEL_NAMES}

    for k in summary:
        text = ' '.join(summary[k][:max_messages])
        summary[k] = f'{text} ... (TRUNCATED ELEMENTS) ...' if len(summary[k]) > max_messages else text

    return '\n'.join([f'{k}: {v}' for k, v in summary.items() if v])


class ChannelTasksAdminSite(admin.AdminSite):
    """
    The base :py:class:`django.contrib.admin.AdminSite` class, providing the necessary context to connect the
    ASGI unit through websocket in order to handle task event notifications.
    """
    site_title = 'Django Channel Tasks Admin'
    site_header = 'Channel Tasks'
    index_title = 'Index'

    def each_context(self, request: HttpRequest):
        """
        Overrides the Django method by adding to the returned context the web-socket URL of the backgroung task unit
        and the cached task events of the user, if any; note this method may be called from the log-in page.
        """
        context = super().each_context(request)
        username = getattr(request.user, 'username')

        if username and request.user.is_authenticated:
            context['cached_task_events'] = TaskCache(username).get_index()
            context['websocket_uri'] = os.path.join('/', settings.CHANNEL_TASKS.proxy_route, 'tasks/clear-cache')
            context['websocket_port'] = os.getenv('CHANNEL_TASKS_ASGI_PORT', 8001)
            context['bootstrap_version'] = os.getenv('BOOTSTRAP_VERSION', '5.3.7')
            context['bootstrap_version_integrity'] = os.getenv('BOOTSTRAP_VERSION_INTEGRITY', 'sha384-ndDqU0Gzau9qJ1lfW4pNLlhNTkCfHzAVBReH9diLvGRem5+R9g2FzA8ZGN954O5Q')

        return context


class ModelTask:
    """
    Callable class whose instances are task coroutines that run concurrently on Django querysets, taking a
    list of database IDs as single argument.
    """

    def __init__(self, app_name: str, model_name: str, instance_task: Callable[[Model], Any]):
        """
        Constructs a coroutine task function that will run the given database-sync function concurrently
        on a set of instances of the specified model.

        :param name: Identifier of the Django App that defines the model.
        :param model_name: Name of the model class.
        :param instance_task: Synchronous task function to run on each instance.
        """
        self.model_class = apps.get_model(app_name, model_name)
        self.instance_task = instance_task

    async def __call__(self, instance_ids: list[int]) -> Any:
        """Runs the coroutine concurrently on the corresponding model instances, and returns the list of outputs."""
        logging.getLogger('django').info(
            'Running %s on %s objects %s...',
            self.instance_task.__name__, self.model_class.__name__, instance_ids,
        )
        outputs = await asyncio.gather(*[self.run(pk) for pk in instance_ids])
        return outputs

    async def run(self, instance_id: int) -> Any:
        try:
            instance = await self.model_class.objects.aget(pk=instance_id)
        except self.model_class.DoesNotExist:
            logging.getLogger('django').error(
                'Instance of %s with pk=%s not found.', self.model_class.__name__, instance_id)
        else:
            try:
                output = await sync_to_async(self.instance_task)(instance)
            except Exception:
                logging.getLogger('django').exception('Got exception:')
            else:
                return output


class AdminTaskAction:
    """
    Callable class whose instances are decorators that produce `django.contrib.admin` action functions that
    schedule, through web-socket, background tasks that will run on the Django queryset selected by the admin user.
    """

    def __init__(self, task_name: str, **kwargs):
        """Constructor.

        :param task_name: Dotted path of a registered task that must take a list of database IDs as single argument.
        :param kwargs: Keyword arguments that are passed directly to the `django.contrib.admin.action` decorator.
        """
        self.task_name = task_name
        self.kwargs = kwargs
        self.client = BackendWebSocketClient()

    def __call__(self,
                 post_schedule_callable: Callable[[admin.ModelAdmin, HttpRequest, QuerySet, WSResponseJSON], Any]
                 ) -> Callable[[admin.ModelAdmin, HttpRequest, QuerySet], Any]:
        """Decorator function.

        :param post_schedule_callable: The decorated function. It takes the same arguments as a regular
          `django.contrib.admin` action function plus the JSON object obtained as response to the web-socket
          schedule request.
        """
        @admin.action(**self.kwargs)
        @functools.wraps(post_schedule_callable)
        def action_callable(modeladmin: admin.ModelAdmin, request: HttpRequest, queryset):
            objects_repr = str(queryset) if queryset.count() > 1 else str(queryset.first())
            ws_response = self.client.perform_request('schedule', [dict(
                registered_task=self.task_name,
                inputs={'instance_ids': list(queryset.values_list('pk', flat=True))}
            )], headers={'Cookie': request.headers['Cookie']})
            description = self.kwargs.get('description', self.task_name)
            msg = f"Requested to '{description}' on {objects_repr}."
            modeladmin.message_user(request, msg, messages.INFO)

            return post_schedule_callable(modeladmin, request, queryset, ws_response)

        return action_callable


class ModelAction(metaclass=abc.ABCMeta):
    def __init__(self, short_description, name=''):
        self.short_description = short_description
        self.__name__ = name or self.__class__.__name__.lower()

    def __call__(self, modeladmin, request, queryset):
        outputs, response = self.run(modeladmin, request, queryset)
        all_outputs = list(outputs)
        ok_outputs = [o for o, level in all_outputs if level == messages.SUCCESS]
        self.ok_message(modeladmin, request, ok_outputs)

        msg = ''.join(f'\n    {ADMIN_LEVELS[level]}: {output}' for output, level in all_outputs)
        mail.mail_admins(
            f'Admin Action performed - {request.POST["action"]}',
            f'{request.method} {request.build_absolute_uri()} {queryset}\n{msg}')

        return response

    def ok_message(self, modeladmin, request, ok_outputs):
        """Send success message given `ok_outputs` list of messages"""

    @abc.abstractmethod
    def run(self, modeladmin, request, queryset):
        """Return (output, level) sequence, response"""


class ModelMethodAction(ModelAction):
    def __init__(self, method_name, short_description='', name=''):
        super().__init__(short_description or method_name, name or method_name)
        self.method_name = method_name

    def run(self, modeladmin, request, queryset):
        return self.outputs(modeladmin, request, queryset), None

    def outputs(self, modeladmin, request, queryset):
        for instance in queryset:
            for output, level in getattr(instance, self.method_name)():
                if level > 29:
                    modeladmin.message_user(request, output, level)
                yield output, level

    def ok_message(self, modeladmin, request, ok_outputs):
        if ok_outputs:
            message = '. '.join([o.strip('.') for o in ok_outputs])
            modeladmin.message_user(request, message, messages.SUCCESS)

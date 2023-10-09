import asyncio
import logging
import time

import django

django.setup()

from django import urls
from django.conf import settings
from django.core.asgi import get_asgi_application

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator

from rest_framework import routers

from django_tasks import models
from django_tasks.admin_tools import ModelTask, register_task
from django_tasks.consumers import TaskEventsConsumer, TasksRestConsumer
from django_tasks.viewsets import TaskViewSet


@register_task
async def sleep_test(duration, raise_error=False):
    logging.getLogger('django').info('Starting sleep test.')
    await asyncio.sleep(duration)

    if raise_error:
        logging.getLogger('django').info('Sleep test done with raise.')
        raise Exception('Test error')

    logging.getLogger('django').info('Sleep test done with no raise.')
    return f"Slept for {duration} seconds"


@register_task
async def doctask_access_test(instance_ids: list[int]):
    def instance_function(doctask):
        time.sleep(1)
        logging.getLogger('django').info('Retrieved %s', repr(doctask))
        time.sleep(1)

    await ModelTask(models.DocTask, instance_function)(instance_ids)
    await asyncio.sleep(4)


@register_task
async def doctask_deletion_test(instance_ids: list[int]):
    def instance_function(doctask):
        time.sleep(1)
        doctask.delete()
        logging.getLogger('django').info('Deleted %s', repr(doctask))
        time.sleep(1)

    await ModelTask(models.DocTask, instance_function)(instance_ids)


class OptionalSlashRouter(routers.SimpleRouter):
    def __init__(self):
        super().__init__()
        self.trailing_slash = '/?'


http_paths = []


if settings.CHANNEL_TASKS.expose_doctask_api is True:
    drf_router = OptionalSlashRouter()
    drf_router.register('tasks', TaskViewSet)
    http_paths.append(urls.re_path(r'^api/', URLRouter(TasksRestConsumer.get_urls(drf_router))))


http_paths.append(urls.re_path(r'^', get_asgi_application()))
url_routers = {
    'http': URLRouter(http_paths),
    'websocket': AllowedHostsOriginValidator(AuthMiddlewareStack(
        URLRouter([urls.path('tasks/', TaskEventsConsumer.as_asgi())])
    )),
}
application = ProtocolTypeRouter(url_routers)

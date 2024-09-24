import asyncio
import logging
import time

from django import urls

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator

from django_tasks import asgi_setup
from django_tasks.admin_tools import ModelTask, register_task
from django_tasks.consumers import TaskEventsConsumer


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

    await ModelTask('django_tasks', 'DocTask', instance_function)(instance_ids)
    await asyncio.sleep(4)


@register_task
async def doctask_deletion_test(instance_ids: list[int]):
    def instance_function(doctask):
        time.sleep(1)
        doctask.delete()
        logging.getLogger('django').info('Deleted %s', repr(doctask))
        time.sleep(1)

    await ModelTask('django_tasks', 'DocTask', instance_function)(instance_ids)


url_routers = {
    'http': asgi_setup.asgi_app,
    'websocket': AllowedHostsOriginValidator(AuthMiddlewareStack(
        URLRouter([urls.path('tasks/', TaskEventsConsumer.as_asgi())])
    )),
}
application = ProtocolTypeRouter(url_routers)

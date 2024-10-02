import asyncio
import logging
import time

from django import urls

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator

from django_tasks import tasks
from django_tasks import asgi_setup
from django_tasks.admin_tools import ModelTask, register_task
from django_tasks.consumers import TaskEventsConsumer


register_task(tasks.sleep_test)
register_task(tasks.doctask_deletion_test)
register_task(tasks.doctask_access_test)


url_routers = {
    'http': asgi_setup.asgi_app,
    'websocket': AllowedHostsOriginValidator(AuthMiddlewareStack(
        URLRouter([urls.path('tasks/', TaskEventsConsumer.as_asgi())])
    )),
}
application = ProtocolTypeRouter(url_routers)

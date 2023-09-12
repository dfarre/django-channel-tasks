import django

django.setup()

from django import urls
from django.conf import settings
from django.core.asgi import get_asgi_application

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator

from rest_framework import routers

from django_tasks.consumers import TaskEventsConsumer, TasksRestConsumer
from django_tasks.viewsets import TaskViewSet


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
    'websocket': AllowedHostsOriginValidator(
        URLRouter([urls.path('tasks/', TaskEventsConsumer.as_asgi())])
    ),
}
application = ProtocolTypeRouter(url_routers)

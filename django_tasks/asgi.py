from django.core.asgi import get_asgi_application
from django import urls

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

from rest_framework import routers

from django_tasks.consumers import TaskEventsConsumer, TasksRestConsumer
from django_tasks.viewsets import TaskViewSet


class OptionalSlashRouter(routers.SimpleRouter):
    def __init__(self):
        super().__init__()
        self.trailing_slash = '/?'


asgi_app = get_asgi_application()

drf_router = OptionalSlashRouter()
drf_router.register('tasks', TaskViewSet)

application = ProtocolTypeRouter(
    {
        "http": URLRouter([
            urls.re_path(r'^api/', URLRouter(TasksRestConsumer.get_urls(drf_router))),
            urls.re_path(r'^', asgi_app),
        ]),
        'websocket': AllowedHostsOriginValidator(AuthMiddlewareStack(
            URLRouter([urls.path('tasks/', TaskEventsConsumer.as_asgi())])
        )),
    }
)

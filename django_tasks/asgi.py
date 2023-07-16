from django.core.asgi import get_asgi_application
from django import urls

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

from django_tasks.consumers import TaskEventsConsumer, TasksRestConsumer
from django_tasks.routers import OptionalSlashRouter
from django_tasks.viewsets import TaskViewSet


drf_router = OptionalSlashRouter()
drf_router.register('api/tasks', TaskViewSet)


application = ProtocolTypeRouter(
    {
        "http": URLRouter([TasksRestConsumer.get_url(url) for url in drf_router.urls] + [
            urls.re_path(r'', get_asgi_application()),
        ]),
        'websocket': AllowedHostsOriginValidator(
            AuthMiddlewareStack(URLRouter([urls.path('tasks/', TaskEventsConsumer.as_asgi())]))
        ),
    }
)

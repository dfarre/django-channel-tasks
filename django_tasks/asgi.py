from django.core.asgi import get_asgi_application
from django.urls import path
from channels.routing import ProtocolTypeRouter, URLRouter

from django_tasks.consumers import TaskStatusConsumer


application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": URLRouter([path("tasks/status/", TaskStatusConsumer.as_asgi())]),
    }
)

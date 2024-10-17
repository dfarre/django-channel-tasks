from django import urls

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator

from django_tasks import asgi_setup
from django_tasks.channels_auth import DRFTokenAuthMiddleware
from django_tasks.consumers import TaskEventsConsumer


url_routers = {
    'http': asgi_setup.application,
    'websocket': AllowedHostsOriginValidator(DRFTokenAuthMiddleware(AuthMiddlewareStack(
        URLRouter([urls.path('tasks/', TaskEventsConsumer.as_asgi())])
    ))),
}
application = ProtocolTypeRouter(url_routers)

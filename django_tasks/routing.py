from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator

from django_tasks.authentication import DRFTokenAuthMiddleware
from django_tasks import urls


application = ProtocolTypeRouter({
    'http': URLRouter([urls.re_path(
        r'^api/', DRFTokenAuthMiddleware(AuthMiddlewareStack(URLRouter(list(urls.get_http_channels_urls())))),
    )]),
    'websocket': AllowedHostsOriginValidator(DRFTokenAuthMiddleware(AuthMiddlewareStack(
        URLRouter(list(urls.get_websocket_urls()))))
    ),
})

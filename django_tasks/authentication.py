import logging

from asgiref.sync import sync_to_async

from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed


class AsyncTokenAuthentication(TokenAuthentication):
    @sync_to_async
    def authenticate_credentials(self, key: str):
        return super().authenticate_credentials(key)

    @sync_to_async
    def authenticate(self, request):
        return super().authenticate(request)


class DRFTokenAuthMiddleware:
    """ASGI application middleware that tries to authenticate by DRF Token."""

    def __init__(self, asgi_app):
        self.asgi_app = asgi_app
        self.token_auth = AsyncTokenAuthentication()

    async def __call__(self, scope, receive, send):
        token_key = self.get_token_key(scope)

        if token_key:
            try:
                user, token = await self.token_auth.authenticate_credentials(token_key)
            except AuthenticationFailed:
                logging.getLogger('django').warning('Invalid token %s.', token_key)
            else:
                scope['user'] = user

        asgi_app = await self.asgi_app(scope, receive, send)
        return asgi_app

    def get_token_key(self, scope):
        for name, value in scope.get('headers', []):
            if name == b'authorization':
                auth_header = value.decode().split()
                if len(auth_header) == 2 and auth_header[0] == self.token_auth.keyword:
                    return auth_header[1]

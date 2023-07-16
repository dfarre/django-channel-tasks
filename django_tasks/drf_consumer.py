import traceback

from channels.db import database_sync_to_async
from channels.generic.http import AsyncHttpConsumer
from django import urls
from rest_framework.test import APIRequestFactory


class DrfConsumer(AsyncHttpConsumer):
    content_type = 'application/json'

    @classmethod
    def as_asgi(cls, *args, **kwargs):
        consumer = super().as_asgi(*args, **kwargs)
        cls.drf_url = kwargs['drf_url']
        return consumer

    @classmethod
    def get_url(cls, drf_url):
        return urls.re_path(str(drf_url.pattern), cls.as_asgi(drf_url=drf_url))

    async def handle(self, body):
        try:
            factory = APIRequestFactory()
            request = getattr(factory, self.scope['method'].lower())(
                self.scope['path'], body, headers={k.decode(): v.decode() for k, v in self.scope['headers']},
                content_type=self.content_type,
            )
            args, kwargs = self.scope['url_route']['args'], self.scope['url_route']['kwargs']
            response = await database_sync_to_async(self.drf_url.callback)(request, *args, **kwargs)
            response.render()

            await self.process_drf_response(response)
            await self.send_response(response.status_code, response.content, headers=[
                (k.encode(), v.encode()) for k, v in response.headers.items()
            ])
        except Exception as exc:
            await self.send_response(500, ''.join(traceback.format_exception(exc)).encode())

    async def process_drf_response(self, drf_response):
        """Overrite for any postprocessing."""

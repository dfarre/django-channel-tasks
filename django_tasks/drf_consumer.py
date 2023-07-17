import logging
import traceback

from channels.db import database_sync_to_async
from channels.generic.http import AsyncHttpConsumer
from channels.routing import URLRouter
from django import urls
from rest_framework import status
from rest_framework.test import APIRequestFactory


class DrfConsumer(AsyncHttpConsumer):
    content_type = 'application/json'

    @classmethod
    def as_asgi(cls, drf_url, *args, **kwargs):
        consumer = super().as_asgi(*args, **kwargs)
        consumer.drf_url = drf_url
        return consumer

    @classmethod
    def get_urls(cls, drf_router, *args, **kwargs):
        return [urls.re_path(str(drf_url.pattern), cls.as_asgi(drf_url)) for drf_url in drf_router.urls]

    @property
    def args(self):
        return self.scope['url_route']['args']

    @property
    def kwargs(self):
        return self.scope['url_route']['kwargs']

    def make_drf_request(self, request_body: bytes):
        factory = APIRequestFactory()
        return getattr(factory, self.scope['method'].lower())(
            self.scope['path'],
            request_body,
            headers={k.decode(): v.decode() for k, v in self.scope['headers']},
            content_type=self.content_type,
        )

    @database_sync_to_async
    def view_coroutine(self, request_body: bytes):
        return self.drf_url.callback(self.make_drf_request(request_body), *self.args, **self.kwargs)

    async def handle(self, body: bytes):
        logging.getLogger('django').info('Handling scope %s with %s', self.scope, self.drf_url)

        try:
            drf_response = await self.view_coroutine(body)
            drf_response.render()
            await self.process_drf_response(drf_response)
            await self.send_response(drf_response.status_code, drf_response.content, headers=[
                (k.encode(), v.encode()) for k, v in drf_response.headers.items()
            ])
        except Exception as exc:
            await self.send_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR, ''.join(traceback.format_exception(exc)).encode()
            )

    async def process_drf_response(self, drf_response):
        """Overrite for any postprocessing."""

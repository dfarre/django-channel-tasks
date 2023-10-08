import traceback

from channels.db import database_sync_to_async
from channels.generic.http import AsyncHttpConsumer

from django import urls
from django.conf import settings

from rest_framework import status
from rest_framework.test import APIRequestFactory


class DrfConsumer(AsyncHttpConsumer):
    content_type = 'application/json'

    def __init__(self, *args, **kwargs):
        self.drf_url = kwargs.pop('drf_url')
        super().__init__(*args, **kwargs)

    @classmethod
    def get_urls(cls, drf_router):
        return [urls.re_path(str(url.pattern), cls.as_asgi(drf_url=url)) for url in drf_router.urls]

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
        try:
            drf_response = await self.view_coroutine(body)
            drf_response.render()
            await self.process_drf_response(drf_response)
            await self.send_response(drf_response.status_code, drf_response.content, headers=[
                (k.encode(), v.encode()) for k, v in drf_response.headers.items()
            ])
        except Exception:
            await self.send_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                traceback.format_exc().encode() if settings.DEBUG else b''
            )

    async def process_drf_response(self, drf_response):
        """Overrite for any postprocessing."""

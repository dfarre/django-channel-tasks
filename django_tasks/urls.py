"""Module providing all URL patterns, after performing the Django setup."""
from django.conf import settings

from rest_framework.routers import SimpleRouter

from django_tasks.django_setup import django
from django_tasks import admin
from django_tasks.viewsets import WSDocTaskViewSet, DocTaskViewSet
from django_tasks.consumers import (
    TaskScheduleHttpConsumer,
    DocTaskScheduleHttpConsumer,
    TaskScheduleWebSocketConsumer,
    DocTaskScheduleWebSocketConsumer,
    CacheClearWebSocketConsumer,
)

path = django.urls.path
re_path = django.urls.re_path


class OptionalSlashRouter(SimpleRouter):
    def __init__(self):
        super().__init__()
        self.trailing_slash = '/?'


def get_wsgi_urls():
    if settings.CHANNEL_TASKS.expose_rest_api is True:
        drf_router = OptionalSlashRouter()
        drf_router.register('doctasks', WSDocTaskViewSet, basename='doctask')
        yield path('api/', django.urls.include(drf_router.urls))

    yield path('admin/', admin.site.urls)


def get_asgi_urls():
    if settings.CHANNEL_TASKS.expose_rest_api is True:
        drf_router = OptionalSlashRouter()
        drf_router.register('adrf/doctasks', DocTaskViewSet, basename='doctask')
        yield from drf_router.urls


def get_http_channels_urls():
    if settings.CHANNEL_TASKS.expose_rest_api is True:
        yield path('doctasks/schedule', DocTaskScheduleHttpConsumer.as_asgi())
        yield path('tasks/schedule', TaskScheduleHttpConsumer.as_asgi())


def get_websocket_urls():
    yield path('tasks/schedule', TaskScheduleWebSocketConsumer.as_asgi())
    yield path('tasks/schedule-store', DocTaskScheduleWebSocketConsumer.as_asgi())
    yield path('tasks/clear-cache', CacheClearWebSocketConsumer.as_asgi())

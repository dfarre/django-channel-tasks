"""Utils module that provides Django URL patterns for the DRF APIs."""
from django import urls

from django.conf import settings

from rest_framework import routers

from django_tasks.viewsets import WSTaskViewSet, TaskViewSet


class OptionalSlashRouter(routers.SimpleRouter):
    def __init__(self):
        super().__init__()
        self.trailing_slash = '/?'


def get_wsgi_urls():
    if settings.CHANNEL_TASKS.expose_doctask_api is True:
        drf_router = OptionalSlashRouter()
        drf_router.register('doctasks', WSTaskViewSet, basename='task')
        yield urls.path('api/', urls.include(drf_router.urls))


def get_asgi_urls():
    if settings.CHANNEL_TASKS.expose_doctask_api is True:
        drf_router = OptionalSlashRouter()
        drf_router.register('doctasklist', TaskViewSet, basename='doctask')
        yield urls.path('api/', urls.include(drf_router.urls))

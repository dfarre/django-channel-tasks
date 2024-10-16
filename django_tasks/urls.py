from django import urls

from django.conf import settings

from rest_framework import routers

from django_tasks import admin
from django_tasks.viewsets import WSTaskViewSet, TaskViewSet


class OptionalSlashRouter(routers.SimpleRouter):
    def __init__(self):
        super().__init__()
        self.trailing_slash = '/?'


urlpatterns = [
    urls.path('admin/', admin.site.urls),
]

if settings.CHANNEL_TASKS.expose_doctask_api is True:
    drf_router = OptionalSlashRouter()
    drf_router.register('doctasks', TaskViewSet, basename='doctask')
    drf_router.register('tasks', WSTaskViewSet, basename='task')
    urlpatterns.append(urls.path('api/', urls.include(drf_router.urls)))

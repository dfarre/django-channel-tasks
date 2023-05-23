from django import urls

from rest_framework import routers

from django_tasks import admin
from django_tasks import views


router = routers.SimpleRouter()

router.register('tasks', views.TaskViewSet)

urlpatterns = [
    urls.path('', urls.include(router.urls)),
    urls.path('', admin.site.urls),
    urls.path('', urls.include('rest_framework.urls')),
]

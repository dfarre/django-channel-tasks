from django import urls

from rest_framework import routers

from django_tasks import views


router = routers.SimpleRouter()

router.register('tasks', views.TaskViewSet)

urlpatterns = [
    urls.path('', urls.include('rest_framework.urls')),
    urls.path('', urls.include(router.urls)),
]

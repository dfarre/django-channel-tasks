"""Django root URL configuration for ASGI deployments."""
from django_tasks import drf_urls

urlpatterns = list(drf_urls.get_asgi_urls())

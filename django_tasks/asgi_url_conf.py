"""Django root URL configuration for ASGI deployments."""
from django_tasks import urls


urlpatterns = list(urls.get_asgi_urls())

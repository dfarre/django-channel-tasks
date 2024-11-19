"""Django root URL configuration for WSGI deployments."""
from django_tasks import urls


urlpatterns = list(urls.get_wsgi_urls())

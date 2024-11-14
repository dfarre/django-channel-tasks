"""Django root URL configuration for WSGI deployments."""
from django import urls

from django_tasks import admin, drf_urls


urlpatterns = list(drf_urls.get_wsgi_urls()) + [urls.path('admin/', admin.site.urls)]

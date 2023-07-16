from django import urls

from django_tasks import admin


urlpatterns = [
    urls.path('', admin.site.urls),
]

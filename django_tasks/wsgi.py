from django.apps import apps
from django.core.wsgi import get_wsgi_application

from django_tasks.tasks import register_django_tasks

application = get_wsgi_application()
register_django_tasks(apps)

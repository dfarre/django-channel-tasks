from django.apps import apps
from django.core.wsgi import get_wsgi_application

from django_tasks import tasks

application = get_wsgi_application()

RegisteredTask = apps.get_model('django_tasks', 'RegisteredTask')
RegisteredTask.register(tasks.sleep_test)
RegisteredTask.register(tasks.doctask_deletion_test)
RegisteredTask.register(tasks.doctask_access_test)

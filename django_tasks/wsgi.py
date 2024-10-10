from django.core.wsgi import get_wsgi_application

from django_tasks import tasks
from django_tasks.admin_tools import register_task

application = get_wsgi_application()

register_task(tasks.sleep_test)
register_task(tasks.doctask_deletion_test)
register_task(tasks.doctask_access_test)

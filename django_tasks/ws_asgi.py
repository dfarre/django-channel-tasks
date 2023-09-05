import os

os.environ['DJANGO_SETTINGS_MODULE'] = 'django_tasks.settings.base'

from django_tasks import asgi  # noqa

application = asgi.application

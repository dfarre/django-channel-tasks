from django_tasks.settings.base import *  # noqa


INSTALLED_APPS.append('django.contrib.postgres')  # noqa

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'postgres',
        'HOST': 'db',
        'PASSWORD': 'postgres',
        'PORT': 5433,
        'USER': 'postgres',
    }
}

DJANGO_TASKS = dict(expose_doctask_api=True, proxy_route='')

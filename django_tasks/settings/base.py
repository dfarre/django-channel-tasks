import os

from typing import Any

from django_tasks.settings import SettingsIni

CHANNEL_TASKS = SettingsIni()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = 'cg2fbx3f)_9znm3$($suorm*0fyuv#wr586195!q^pv0%ct7c5'

DEBUG = CHANNEL_TASKS.debug

ALLOWED_HOSTS: list[str] = CHANNEL_TASKS.allowed_hosts

INSTALLED_APPS: list[str] = [
    'bootstrap5',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'rest_framework.authtoken',
    'rest_framework',
    'django.contrib.messages',
    'django_tasks.apps.TasksConfig',
    'django_extensions',
    'django_filters',
    'django.contrib.postgres',
]

MIDDLEWARE: list[str] = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'request_logging.middleware.LoggingMiddleware',
]

DJANGO_LOG_LEVEL = CHANNEL_TASKS.log_level

LOGGING = dict(
    version=1,
    disable_existing_loggers=False,
    handlers={
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'thread-logname',
        },
        'console-debug': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    formatters={
        'verbose': {
            'format': '{levelname} {asctime} {threadName} ({pathname}) {funcName}:L{lineno} ★ {message}',
            'style': '{',
        },
        'thread-logname': {
            'format': '{levelname} {asctime} ({threadName}) {name} ★ {message}',
            'style': '{',
        },
    },
    loggers={
        'django': {
            'level': DJANGO_LOG_LEVEL,
            'handlers': ['console-debug'],
        },
        'django.request': {
            'handlers': ['console'],
            'level': DJANGO_LOG_LEVEL,
            'propagate': False,
        },
        'django.channels': {
            'handlers': ['console'],
            'level': DJANGO_LOG_LEVEL,
            'propagate': False,
        },
    },
)

ROOT_URLCONF = 'django_tasks.urls'

TEMPLATES: list[dict[str, Any]] = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

ASGI_APPLICATION = 'django_tasks.ws_asgi.application'

DATABASES: dict[str, Any] = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'postgres',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': 'db',
        'PORT': 5433,
    }
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

AUTHENTICATION_BACKENDS: list[str] = [
    "django.contrib.auth.backends.ModelBackend",
]

SESAME_MAX_AGE = 86400*5

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/Madrid'

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

REST_FRAMEWORK = dict(
    DEFAULT_RENDERER_CLASSES=(
        'rest_framework.renderers.JSONRenderer',
    ),
    DEFAULT_PAGINATION_CLASS='rest_framework.pagination.PageNumberPagination',
    DEFAULT_FILTER_BACKENDS=('django_filters.rest_framework.DjangoFilterBackend',),
    DEFAULT_AUTHENTICATION_CLASSES=(
        'rest_framework.authentication.TokenAuthentication',
    ),
    DEFAULT_PERMISSION_CLASSES=(
        'rest_framework.permissions.IsAuthenticated',
    ),
    TEST_REQUEST_DEFAULT_FORMAT='json',
)

CHANNEL_LAYERS = dict(default={
    "BACKEND": "channels_redis.core.RedisChannelLayer",
    "CONFIG": {
        "hosts": [("redis", 6379)],
    },
})

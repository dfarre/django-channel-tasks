import logging

from typing import Any

from django_tasks.settings import SettingsIni


CHANNEL_TASKS = SettingsIni()

DEBUG = CHANNEL_TASKS.debug
SECRET_KEY = CHANNEL_TASKS.secret_key
ALLOWED_HOSTS: list[str] = CHANNEL_TASKS.allowed_hosts

DATABASES: dict[str, Any] = CHANNEL_TASKS.databases
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

INSTALLED_APPS: list[str] = CHANNEL_TASKS.sort_installed_apps('django_tasks.apps.TasksConfig')

CHANNEL_LAYERS = CHANNEL_TASKS.channel_layers

DJANGO_LOG_LEVEL = CHANNEL_TASKS.log_level
REQUEST_LOGGING_DATA_LOG_LEVEL = logging.INFO
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

STATIC_URL = '/static/'
STATIC_ROOT = CHANNEL_TASKS.static_root
MEDIA_URL = '/media/'
MEDIA_ROOT = CHANNEL_TASKS.media_root

(EMAIL_HOST,
 EMAIL_PORT,
 EMAIL_USE_TLS,
 EMAIL_HOST_USER,
 EMAIL_HOST_PASSWORD) = CHANNEL_TASKS.email_settings

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

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/Madrid'

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

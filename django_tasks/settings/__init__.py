"""
This module defines the :py:class:`django_tasks.settings.SettingsJson` class, and the Django settings modules
`django_tasks.settings.asgi`, `django_tasks.settings.wsgi` for the corresponding types of deployment; these
modules are intended for both testing and production deployments, and are configured from
a :py:class:`~django_tasks.settings.SettingsJson` instance.
"""
import importlib.util
import json
import os

from django.core.exceptions import ImproperlyConfigured

from django_tasks.typing import JSON, is_string_key_dict, is_string_key_dict_list, is_string_list


class SettingsJson:
    """
    Class in charge of providing Django setting values, as specified in a JSON settings file whose values override
    the default values provided here.
    """
    json_key: str = 'CHANNEL_TASKS_SETTINGS_PATH'
    secret_key_key: str = 'DJANGO_SECRET_KEY'
    channel_tasks_appname: str = 'django_tasks'
    default_installed_apps: list[str] = [
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.staticfiles',
        'rest_framework.authtoken',
        'adrf',
        'django.contrib.messages',
        'django_extensions',
        'django_filters',
        channel_tasks_appname,
        'django.contrib.admin',
        'django_sass_compiler',
    ]
    default_drf: dict[str, JSON] = dict(
        DEFAULT_RENDERER_CLASSES=[
            'rest_framework.renderers.JSONRenderer',
        ],
        DEFAULT_PAGINATION_CLASS='rest_framework.pagination.PageNumberPagination',
        DEFAULT_FILTER_BACKENDS=[
            'django_filters.rest_framework.DjangoFilterBackend',
        ],
        DEFAULT_AUTHENTICATION_CLASSES=[
            'rest_framework.authentication.TokenAuthentication',
        ],
        DEFAULT_PERMISSION_CLASSES=[
            'rest_framework.permissions.IsAuthenticated',
        ],
        TEST_REQUEST_DEFAULT_FORMAT='json',
    )
    default_middleware: list[str] = [
        'django.middleware.security.SecurityMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
        'request_logging.middleware.LoggingMiddleware',
    ]
    default_auth_password_validators: list[dict[str, JSON]] = [
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
    default_authentication_backends: list[str] = [
        'django.contrib.auth.backends.ModelBackend',
    ]

    @classmethod
    def get_default_templates(cls) -> list[dict[str, JSON]]:
        return [
            {
                'BACKEND': 'django.template.backends.django.DjangoTemplates',
                'DIRS': [f"{os.path.dirname(importlib.util.find_spec(cls.channel_tasks_appname).origin)}/templates"],
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

    @staticmethod
    def get_default_logging(log_level: str) -> dict[str, JSON]:
        return dict(
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
                    'level': log_level,
                    'handlers': ['console-debug'],
                },
                'django.request': {
                    'handlers': ['console'],
                    'level': log_level,
                    'propagate': False,
                },
                'django.channels': {
                    'handlers': ['console'],
                    'level': log_level,
                    'propagate': False,
                },
            },
        )

    def __init__(self):
        self.json_path: str = os.getenv(self.json_key, '')

        if not os.path.isfile(self.json_path):
            raise ImproperlyConfigured(f'Channel-tasks settings file at {self.json_key}={self.json_path} not found.')

        with open(self.json_path) as json_file:
            self.jsonlike: dict[str, JSON] = json.load(json_file)

        if self.secret_key_key not in os.environ:
            raise ImproperlyConfigured(f'Expected a Django secret key in {self.secret_key_key} envvar.')

        self.secret_key: str = os.environ[self.secret_key_key]

    def wrong_type_error(self, key: str, type_repr: str) -> ImproperlyConfigured:
        """
        Constructs and returns a :py:class:`django.core.exceptions.ImproperlyConfigured` exception,
        indicating, with `type_repr`, the required type for the `key` entry.
        """
        return ImproperlyConfigured(f"Setting value for '{key}' must be of type '{type_repr}' in {self.json_path}")

    def get_boolean(self, key: str, default: bool) -> bool:
        """
        Returns a type-checked boolean from the `key` entry,
        or raises :py:class:`django.core.exceptions.ImproperlyConfigured`.
        """
        value = self.jsonlike.get(key, default)

        if not isinstance(value, bool):
            raise self.wrong_type_error(key, 'bool')

        return value

    def get_int(self, key: str, default: int) -> int:
        """
        Returns a type-checked integer from the `key` entry,
        or raises :py:class:`django.core.exceptions.ImproperlyConfigured`.
        """
        value = self.jsonlike.get(key, default)

        if not isinstance(value, int):
            raise self.wrong_type_error(key, 'int')

        return value

    def get_string(self, key: str, default: str) -> str:
        """
        Returns a type-checked string from the `key` entry,
        or raises :py:class:`django.core.exceptions.ImproperlyConfigured`.
        """
        value = self.jsonlike.get(key, default)

        if not isinstance(value, str):
            raise self.wrong_type_error(key, 'str')

        return value

    def get_string_list(self, key: str, default: list[str]) -> list[str]:
        """
        Returns a type-checked list of strings from the `key` entry,
        or raises :py:class:`django.core.exceptions.ImproperlyConfigured`.
        """
        value = self.jsonlike.get(key, default)

        if not is_string_list(value):
            raise self.wrong_type_error(key, 'list[str]')

        return value

    def get_dict(self, key: str, default: dict[str, JSON]) -> dict[str, JSON]:
        """
        Returns a type-checked string-key dictionary from the `key` entry,
        or raises :py:class:`django.core.exceptions.ImproperlyConfigured`.
        """
        value = self.jsonlike.get(key, default)

        if not is_string_key_dict(value):
            raise self.wrong_type_error(key, 'dict[str]')

        return value

    def get_dict_list(self, key: str, default: list[dict[str, JSON]]) -> list[dict[str, JSON]]:
        """
        Returns a type-checked list of string-key dictionaries from the `key` entry,
        or raises :py:class:`django.core.exceptions.ImproperlyConfigured`.
        """
        value = self.jsonlike.get(key, default)

        if not is_string_key_dict_list(value):
            raise self.wrong_type_error(key, 'list[dict[str]]')

        return value

    @property
    def server_name(self) -> str:
        return self.get_string('server-name', 'localhost')

    @property
    def allowed_hosts(self) -> list[str]:
        return ['127.0.0.1', self.server_name]

    @property
    def install_apps(self) -> list[str]:
        return self.get_string_list('install-apps', [])

    @property
    def debug(self) -> bool:
        return self.get_boolean('debug', False)

    @property
    def proxy_route(self) -> str:
        return str(self.jsonlike.get('proxy-route', ''))

    @property
    def local_port(self) -> int:
        return self.get_int('local-port', 8001)

    @property
    def log_level(self) -> str:
        return self.get_string('log-level', 'INFO')

    @property
    def logging(self) -> dict[str, JSON]:
        return self.get_dict('logging', self.get_default_logging(self.log_level))

    @property
    def middleware(self) -> list[str]:
        return self.get_string_list('middleware', self.default_middleware)

    @property
    def templates(self) -> list[dict[str, JSON]]:
        return self.get_dict_list('templates', self.get_default_templates())

    @property
    def language_code(self) -> str:
        return self.get_string('language-code', 'en-gb')

    @property
    def time_zone(self) -> str:
        return self.get_string('time-zone', 'UTC')

    @property
    def auth_password_validators(self) -> list[dict[str, JSON]]:
        return self.get_dict_list('auth-password-validators', self.default_auth_password_validators)

    @property
    def authentication_backends(self) -> list[str]:
        return self.get_string_list('authentication-backends', self.default_authentication_backends)

    @property
    def rest_framework(self) -> dict[str, JSON]:
        return self.get_dict('rest-framework', self.default_drf)

    @property
    def expose_doctask_api(self) -> bool:
        return self.get_boolean('expose-doctask-api', False)

    @property
    def databases(self) -> dict[str, dict[str, JSON]]:
        default_db = self.get_dict('database', {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'channel-tasks.sqlite3',
        })
        db_settings: dict[str, dict[str, JSON]] = {'default': {k.upper(): v for k, v in default_db.items()}}
        db_settings['default'].setdefault('PASSWORD', os.getenv('CHANNEL_TASKS_DB_PASSWORD', ''))

        return db_settings

    @property
    def default_auto_field(self) -> str:
        return self.get_string('default-auto-field', 'django.db.models.BigAutoField')

    @property
    def channel_layers(self) -> dict[str, JSON]:
        return {
            'default': {
                'BACKEND': 'channels_redis.core.RedisChannelLayer',
                'CONFIG': {
                    'hosts': [[self.redis_host, self.redis_port]],
                },
            },
        }

    @property
    def caches(self) -> dict[str, JSON]:
        return {
            'default': {
                'BACKEND': 'django.core.cache.backends.redis.RedisCache',
                'LOCATION': f'redis://{self.redis_host}:{self.redis_port}',
                'TIMEOUT': 4*86400,
            },
        }

    @property
    def redis_host(self) -> str:
        return self.get_string('redis-host', '127.0.0.1')

    @property
    def channel_group(self) -> str:
        return self.get_string('redis-channel-group', 'tasks')

    @property
    def redis_port(self) -> int:
        return self.get_int('redis-port', 6379)

    @property
    def static_root(self) -> str:
        return self.get_string('static-root', '/www/django_tasks/static')

    @property
    def media_root(self) -> str:
        return self.get_string('media-root', '/www/django_tasks/media')

    @property
    def static_url(self) -> str:
        return self.get_string('static-url', '/static/')

    @property
    def media_url(self) -> str:
        return self.get_string('media-url', '/media/')

    @property
    def email_settings(self) -> tuple[str, int, bool, str, str]:
        return (self.email_host,
                self.email_port,
                self.email_use_tls,
                os.getenv('CHANNEL_TASKS_EMAIL_USER', ''),
                os.getenv('CHANNEL_TASKS_EMAIL_PASSWORD', ''))

    @property
    def email_host(self) -> str:
        return self.get_string('email-host', '')

    @property
    def email_port(self) -> int:
        return self.get_int('email-port', 0)

    @property
    def email_use_tls(self) -> bool:
        return self.get_boolean('email-use-tls', False)

    def sort_installed_apps(self, *apps: str) -> list[str]:
        return self.default_installed_apps + [
            k for k in apps if k not in self.default_installed_apps] + self.install_apps

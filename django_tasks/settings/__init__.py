import json
import os

from django.core.exceptions import ImproperlyConfigured

from django_tasks.typing import JSON


class SettingsJson:
    json_key: str = 'CHANNEL_TASKS_SETTINGS_PATH'
    secret_key_key: str = 'DJANGO_SECRET_KEY'
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
        'django_tasks',
        'django.contrib.admin',
        'django_sass_compiler',
    ]

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

        if not (isinstance(value, list) and all(isinstance(a, str) for a in value)):
            raise self.wrong_type_error(key, 'list[str]')

        return value

    def get_dict(self, key: str, default: dict[str, JSON]) -> dict[str, JSON]:
        """
        Returns a type-checked string-key dictionary from the `key` entry,
        or raises :py:class:`django.core.exceptions.ImproperlyConfigured`.
        """
        value = self.jsonlike.get(key, default)

        if not (isinstance(value, dict) and all(isinstance(k, str) for k in value)):
            raise self.wrong_type_error(key, 'dict[str]')

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

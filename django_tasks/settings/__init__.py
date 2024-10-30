import json
import os

from typing import Any


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
        json_path: str = os.getenv(self.json_key, '')
        assert os.path.isfile(json_path), f'Channel-tasks settings file at {self.json_key}={json_path} not found.'

        with open(json_path) as json_file:
            self.jsonlike: dict = json.load(json_file)

        assert self.secret_key_key in os.environ, f'Expected a Django secret key in {self.secret_key_key} envvar.'
        self.secret_key: str = os.environ[self.secret_key_key]

    @property
    def allowed_hosts(self) -> list[str]:
        return ['127.0.0.1', self.server_name]

    @property
    def install_apps(self) -> list[str]:
        return self.jsonlike.get('install-apps', [])

    @property
    def debug(self) -> bool:
        return self.jsonlike.get('debug', False)

    @property
    def server_name(self) -> str:
        return self.jsonlike.get('server-name', 'localhost')

    @property
    def proxy_route(self) -> str:
        return self.jsonlike.get('proxy-route', '')

    @property
    def local_port(self) -> int:
        return self.jsonlike.get('local-port', 8001)

    @property
    def log_level(self) -> str:
        return self.jsonlike.get('log-level', 'INFO')

    @property
    def expose_doctask_api(self) -> bool:
        return self.jsonlike.get('expose-doctask-api', False)

    @property
    def databases(self) -> dict[str, Any]:
        if 'database' not in self.jsonlike:
            return {
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': 'channel-tasks.sqlite3',
                }
            }

        default = {k.upper(): v for k, v in self.jsonlike['database'].items()}
        default.setdefault('PASSWORD', os.getenv('CHANNEL_TASKS_DB_PASSWORD', ''))

        return {'default': default}

    @property
    def channel_layers(self) -> dict[str, Any]:
        return {
            'default': {
                'BACKEND': 'channels_redis.core.RedisChannelLayer',
                'CONFIG': {
                    'hosts': [(self.redis_host, self.redis_port)],
                },
            },
        }

    @property
    def caches(self) -> dict[str, Any]:
        return {
            'default': {
                'BACKEND': 'django.core.cache.backends.redis.RedisCache',
                'LOCATION': f'redis://{self.redis_host}:{self.redis_port}',
                'TIMEOUT': 4*86400,
            },
        }

    @property
    def redis_host(self) -> str:
        return self.jsonlike.get('redis-host', '127.0.0.1')

    @property
    def channel_group(self) -> str:
        return self.jsonlike.get('redis-channel-group', 'tasks')

    @property
    def redis_port(self) -> int:
        return self.jsonlike.get('redis-port', 6379)

    @property
    def static_root(self) -> str:
        return self.jsonlike.get('static-root', '/www/django_tasks/static')

    @property
    def media_root(self) -> str:
        return self.jsonlike.get('media-root', '/www/django_tasks/media')

    @property
    def email_settings(self) -> tuple[str, int, bool, str, str]:
        return (self.email_host,
                self.email_port,
                self.email_use_tls,
                os.getenv('CHANNEL_TASKS_EMAIL_USER', ''),
                os.getenv('CHANNEL_TASKS_EMAIL_PASSWORD', ''))

    @property
    def email_host(self) -> str:
        return self.jsonlike.get('email-host', '')

    @property
    def email_port(self) -> int:
        return self.jsonlike.get('email-port', 0)

    @property
    def email_use_tls(self) -> bool:
        return self.jsonlike.get('email-use-tls', False)

    def sort_installed_apps(self, *apps: str) -> list[str]:
        return self.default_installed_apps + [
            k for k in apps if k not in self.default_installed_apps] + self.install_apps

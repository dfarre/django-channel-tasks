import configparser
import os


class SettingsIni:
    ini_key = 'CHANNEL_TASKS_INI_PATH'
    secret_key_key = 'DJANGO_SECRET_KEY'
    default_installed_apps = [
        'bootstrap5',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.staticfiles',
        'django.contrib.admin',
        'rest_framework.authtoken',
        'rest_framework',
        'django.contrib.messages',
        'django_extensions',
        'django_filters',
    ]

    def __init__(self):
        ini_path = os.getenv(self.ini_key, '')
        assert os.path.isfile(ini_path), f'Channel-tasks settings file at {self.ini_key}={ini_path} not found.'
        self.ini = configparser.ConfigParser()
        self.ini.read(ini_path)

        assert self.secret_key_key in os.environ, f'Expected a Django secret key in {self.secret_key_key} envvar.'
        self.secret_key = os.environ[self.secret_key_key]

    def get_array(self, section, key, default):
        return ([line.strip() for line in self.ini[section][key].splitlines() if line.strip()]
                if self.ini.has_option(section, key) else default)

    def get_boolean(self, section, key, default):
        return self.ini[section].getboolean(key, default) if self.ini.has_section(section) else default

    def get_int(self, section, key, default):
        return self.ini[section].getint(key, default) if self.ini.has_section(section) else default

    def get_text(self, section, key, default):
        return self.ini[section][key].strip() if self.ini.has_option(section, key) else default

    @property
    def allowed_hosts(self):
        return ['127.0.0.1', self.server_name]

    @property
    def install_apps(self):
        return self.get_array('apps', 'install-apps', [])

    @property
    def debug(self):
        return self.get_boolean('security', 'debug', False)

    @property
    def server_name(self):
        return self.get_text('security', 'server-name', 'localhost')

    @property
    def proxy_route(self):
        return self.get_text('security', 'proxy-route', '')

    @property
    def local_port(self):
        return self.get_int('security', 'local-port', 8001)

    @property
    def log_level(self):
        return self.get_text('logging', 'log-level', 'INFO')

    @property
    def expose_doctask_api(self):
        return self.get_boolean('asgi', 'expose-doctask-api', False)

    @property
    def databases(self):
        if not self.ini.has_section('database'):
            return {
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': 'channel-tasks.sqlite3',
                }
            }

        default = {k.upper(): v for k, v in dict(self.ini['database']).items()}
        default.setdefault('PASSWORD', os.getenv('CHANNEL_TASKS_DB_PASSWORD', ''))

        return {'default': default}

    @property
    def channel_layers(self):
        return {
            'default': {
                'BACKEND': 'channels_redis.core.RedisChannelLayer',
                'CONFIG': {
                    'hosts': [(self.redis_host, self.redis_port)],
                },
            },
        }

    @property
    def redis_host(self):
        return self.get_text('redis', 'host', '127.0.0.1')

    @property
    def redis_port(self):
        return self.get_int('redis', 'port', 6379)

    @property
    def static_root(self):
        return self.get_text('security', 'static-root', '/www/django_tasks/static')

    @property
    def media_root(self):
        return self.get_text('security', 'media-root', '/www/django_tasks/media')

    @property
    def email_settings(self):
        return (self.email_host,
                self.email_port,
                self.email_use_tls,
                os.getenv('CHANNEL_TASKS_EMAIL_USER', ''),
                os.getenv('CHANNEL_TASKS_EMAIL_PASSWORD', ''))

    @property
    def email_host(self):
        return self.get_text('email', 'host', '')

    @property
    def email_port(self):
        return self.get_int('email', 'port', 0)

    @property
    def email_use_tls(self):
        return self.get_boolean('email', 'use-tls', False)


    def sort_installed_apps(self, *apps: list[str]) -> list[str]:
        return self.default_installed_apps + [
            k for k in apps if k not in self.default_installed_apps] + self.install_apps

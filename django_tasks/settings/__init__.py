import configparser
import os
import pkg_resources


class SettingsIni:
    def __init__(self):
        self.package_name = os.getenv('CHANNEL_TASKS_MAIN_MODULE', 'django_tasks')
        self.ini_rel_path = os.getenv('CHANNEL_TASKS_INI_REL_PATH', 'settings/channel-task-defaults.ini')
        self.ini = configparser.ConfigParser()
        self.ini.read(pkg_resources.resource_filename(self.package_name, self.ini_rel_path))

    def get_array(self, section, key, default):
        return ([line.strip() for line in self.ini[section][key].splitlines()]
                if self.ini.has_option(section, key) else default)

    def get_boolean(self, section, key, default):
        return self.ini[section].getboolean(key, default) if self.ini.has_section(section) else default

    def get_text(self, section, key, default):
        return self.ini[section][key].strip() if self.ini.has_option(section, key) else default

    @property
    def allowed_hosts(self):
        return self.get_array('security', 'allowed-hosts', ['localhost'])

    @property
    def debug(self):
        return self.get_boolean('security', 'debug', False)

    @property
    def proxy_route(self):
        return self.get_text('security', 'proxy-route', '')

    @property
    def expose_doctask_api(self):
        return self.get_boolean('asgi', 'expose-doctask-api', False)

    def set_databases(self, settings):
        if not self.ini.has_section('database'):
            return

        default = dict(self.ini['database'])

        if 'install-apps' in default:
            install_apps = [s.strip() for s in default.pop('install-apps').strip().splitlines()]
            settings.INSTALLED_APPS.extend(install_apps)

        settings.DATABASES = dict(default={k.upper(): v for k, v in default.items()})

    def apply(self, settings):
        settings.ALLOWED_HOSTS = self.allowed_hosts
        settings.DEBUG = self.debug
        self.set_databases(settings)

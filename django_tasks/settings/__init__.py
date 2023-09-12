import configparser
import os
import pkg_resources


class SettingsIni:
    def __init__(self):
        self.package_name = os.getenv('CHANNEL_TASKS_MAIN_MODULE', 'django_tasks')
        self.ini_rel_path = os.getenv('CHANNEL_TASKS_INI_REL_PATH', 'settings/channel-task-defaults.ini')
        self.ini = configparser.ConfigParser()
        self.ini.read(pkg_resources.resource_filename(self.package_name, self.ini_rel_path))

    @property
    def allowed_hosts(self):
        section, key = 'security', 'allowed-hosts'
        return ([line.strip() for line in self.ini[section][key].splitlines()]
                if self.ini.has_option(section, key) else ['localhost'])

    @property
    def proxy_route(self):
        section, key = 'security', 'proxy-route'
        return self.ini[section][key].strip() if self.ini.has_option(section, key) else ''

    @property
    def expose_doctask_api(self):
        section, key = 'asgi', 'expose-doctask-api'
        return self.ini[section].getboolean(key, False) if self.ini.has_section(section) else False

    def apply(self, settings):
        pass

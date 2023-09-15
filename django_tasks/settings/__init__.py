import configparser
import os


class SettingsIni:
    def __init__(self):
        ini_key = 'CHANNEL_TASKS_INI_PATH'
        assert ini_key in os.environ, f'Settings are to be specified with the {ini_key} envvar.'
        self.ini = configparser.ConfigParser()
        self.ini.read(os.environ[ini_key])

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
    def log_level(self):
        return self.get_text('logging', 'log-level', 'INFO')

    @property
    def expose_doctask_api(self):
        return self.get_boolean('asgi', 'expose-doctask-api', False)

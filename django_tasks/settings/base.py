import sys
import logging

from django_tasks.settings import SettingsJson


CHANNEL_TASKS = SettingsJson()

for name, value in CHANNEL_TASKS.other_settings.items():
    setattr(sys.modules[__name__], name, value)

DEBUG = CHANNEL_TASKS.debug
SECRET_KEY = CHANNEL_TASKS.secret_key
ALLOWED_HOSTS = CHANNEL_TASKS.allowed_hosts

LANGUAGE_CODE = CHANNEL_TASKS.language_code
TIME_ZONE = CHANNEL_TASKS.time_zone

DATABASES = CHANNEL_TASKS.databases
DEFAULT_AUTO_FIELD = CHANNEL_TASKS.default_auto_field

INSTALLED_APPS = CHANNEL_TASKS.installed_apps

MIDDLEWARE = CHANNEL_TASKS.middleware

TEMPLATES = CHANNEL_TASKS.templates

CHANNEL_LAYERS = CHANNEL_TASKS.channel_layers
CACHES = CHANNEL_TASKS.caches

AUTHENTICATION_BACKENDS = CHANNEL_TASKS.authentication_backends
AUTH_PASSWORD_VALIDATORS = CHANNEL_TASKS.auth_password_validators

REST_FRAMEWORK = CHANNEL_TASKS.rest_framework

REQUEST_LOGGING_DATA_LOG_LEVEL = logging.INFO
LOGGING = CHANNEL_TASKS.logging

STATIC_URL = CHANNEL_TASKS.static_url
STATIC_ROOT = CHANNEL_TASKS.static_root
MEDIA_URL = CHANNEL_TASKS.media_url
MEDIA_ROOT = CHANNEL_TASKS.media_root

(EMAIL_HOST,
 EMAIL_PORT,
 EMAIL_USE_TLS,
 EMAIL_HOST_USER,
 EMAIL_HOST_PASSWORD) = CHANNEL_TASKS.email_settings

JAZZMIN_SETTINGS = CHANNEL_TASKS.jazzmin
JAZZMIN_UI_TWEAKS = CHANNEL_TASKS.jazzmin_ui_tweaks

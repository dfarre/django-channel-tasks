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
    #: Name of the environment variable that holds the path to the settings JSON file.
    json_key: str = 'CHANNEL_TASKS_SETTINGS_PATH'

    #: Name of the environment variable that holds the Django secret key.
    secret_key_key: str = 'DJANGO_SECRET_KEY'

    #: Name of the channel-tasks Django app.
    channel_tasks_appname: str = 'django_tasks'

    #: List of identifiers of the Django apps that must be intalled. The "install-apps" setting may be
    #: specified with an array of additional apps to install.
    required_installed_apps: list[str] = [
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.staticfiles',
        'rest_framework.authtoken',
        'adrf',
        'django.contrib.messages',
        'django_filters',
        channel_tasks_appname,
        'jazzmin',
        'django.contrib.admin',
    ]

    #: Default DRF settings, may be overriden with care using the "rest-framework" setting.
    default_drf: dict[str, JSON] = dict(
        DEFAULT_RENDERER_CLASSES=[
            'rest_framework.renderers.JSONRenderer',
        ],
        DEFAULT_PARSER_CLASSES=[
            'rest_framework.parsers.JSONParser',
        ],
        DEFAULT_PAGINATION_CLASS='rest_framework.pagination.LimitOffsetPagination',
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

    #: Sequence of middleware specifications required for secure deployments. The "append-middleware" setting
    #: may be specified with an array of additional middleware.
    required_middleware: list[str] = [
        'django.middleware.security.SecurityMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
    ]

    #: Default auth password validators, may be overriden with care using "auth-password-validators".
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

    #: Default auth backends, may be overriden with care using "authentication-backends".
    default_authentication_backends: list[str] = [
        'django.contrib.auth.backends.ModelBackend',
    ]

    @classmethod
    def get_default_templates(cls) -> list[dict[str, JSON]]:
        """Returns the Django TEMPLATES setting value that will be set by default.

        This value may be overriden, with care, using the "templates" setting."""
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
    def other_settings(self) -> str:
        """Dictionary of additional settings, empty by default."""
        return self.get_dict('other-settings', {})

    @property
    def allowed_hosts(self) -> list[str]:
        """Will be set as the Django ALLOWED_HOSTS setting value.

        Only the loopback address, for local websocket connections, and the configured "server-name" will be allowed."""
        return ['127.0.0.1', self.server_name]

    @property
    def server_name(self) -> str:
        """The configured "server-name" value. Defaults to localhost."""
        return self.get_string('server-name', 'localhost')

    @property
    def install_apps(self) -> list[str]:
        """The configured "install-apps" value. Defaults to empty array (no additional apps)."""
        return self.get_string_list('install-apps', [])

    @property
    def jazzmin(self) -> JSON:
        """The configured "jazzmin" value, with a default django-admin theme. Will be set as the JAZZMIN_SETTINGS settings value."""
        return self.get_dict('jazzmin',  {
            # title of the window (Will default to current_admin_site.site_title if absent or None)
            "site_title": "Django Channel Tasks Admin",

            # Title on the login screen (19 chars max) (defaults to current_admin_site.site_header if absent or None)
            "site_header": "Django Channel Tasks",

            # Title on the brand (19 chars max) (defaults to current_admin_site.site_header if absent or None)
            "site_brand": "Django Admin",

            # Logo to use for your site, must be present in static files, used for login form logo (defaults to site_logo)
            "login_logo": None,

            # Logo to use for login form in dark themes (defaults to login_logo)
            "login_logo_dark": None,

            # CSS classes that are applied to the logo above
            "site_logo_classes": "img-circle",

            # Relative path to a favicon for your site, will default to site_logo if absent (ideally 32x32 px)
            "site_icon": None,

            # Welcome text on the login screen
            "welcome_sign": "Welcome to the Django Channel Tasks Admin Site",

            # Copyright on the footer
            "copyright": "Daniel Farré Manzorro",

            # List of model admins to search from the search bar, search bar omitted if excluded
            # If you want to use a single search field you dont need to use a list, you can use a simple string
            "search_model": ["django_tasks.DocTask", "django_tasks.RegisteredTask"],

            # Field name on user model that contains avatar ImageField/URLField/Charfield or a callable that receives the user
            "user_avatar": None,

            ############
            # Top Menu #
            ############
            # Links to put along the top menu
            "topmenu_links": [
                # Url that gets reversed (Permissions can be added)
                {"name": "Home",  "url": "admin:index", "permissions": ["auth.view_user"]},

                # model admin to link to (Permissions checked against model)
                {"model": "auth.User"},
            ],

            #############
            # User Menu #
            #############
            # Additional links to include in the user menu on the top right ("app" url type is not allowed)
            "usermenu_links": [
                {"model": "auth.user"}
            ],

            #############
            # Side Menu #
            #############
            # Whether to display the side menu
            "show_sidebar": True,

            # Whether to aut expand the menu
            "navigation_expanded": True,

            # Hide these apps when generating side menu e.g (auth)
            "hide_apps": [],

            # Hide these models when generating side menu (e.g auth.user)
            "hide_models": [],

            # List of apps (and/or models) to base side menu ordering off of (does not need to contain all apps/models)
            "order_with_respect_to": ["auth"],

            # Custom links to append to app groups, keyed on app name
            "custom_links": {
                # "books": [{
                #     "name": "Make Messages",
                #     "url": "make_messages",
                #     "icon": "fas fa-comments",
                #     "permissions": ["books.view_book"]
                # }]
            },

            # Custom icons for side menu apps/models See https://fontawesome.com/icons?d=gallery&m=free&v=5.0.0,5.0.1,5.0.10,5.0.11,5.0.12,5.0.13,5.0.2,5.0.3,5.0.4,5.0.5,5.0.6,5.0.7,5.0.8,5.0.9,5.1.0,5.1.1,5.2.0,5.3.0,5.3.1,5.4.0,5.4.1,5.4.2,5.13.0,5.12.0,5.11.2,5.11.1,5.10.0,5.9.0,5.8.2,5.8.1,5.7.2,5.7.1,5.7.0,5.6.3,5.5.0,5.4.2
            # for the full list of 5.13.0 free icon classes
            "icons": {
                "auth": "fas fa-users-cog",
                "auth.user": "fas fa-user",
                "auth.Group": "fas fa-users",
            },

            # Icons that are used when one is not manually specified
            "default_icon_parents": "fas fa-chevron-circle-right",
            "default_icon_children": "fas fa-circle",

            #################
            # Related Modal #
            #################
            # Use modals instead of popups
            "related_modal_active": False,

            #############
            # UI Tweaks #
            #############
            # Relative paths to custom CSS/JS scripts (must be present in static files)
            "custom_css": None,
            "custom_js": None,
            # Whether to link font from fonts.googleapis.com (use custom_css to supply font otherwise)
            "use_google_fonts_cdn": True,
            # Whether to show the UI customizer on the sidebar
            "show_ui_builder": False,

            ###############
            # Change view #
            ###############
            # Render out the change view as a single form, or in tabs, current options are
            # - single
            # - horizontal_tabs (default)
            # - vertical_tabs
            # - collapsible
            # - carousel
            "changeform_format": "horizontal_tabs",
            # override change forms on a per modeladmin basis
            "changeform_format_overrides": {"auth.user": "collapsible", "auth.group": "vertical_tabs"},
        })

    @property
    def jazzmin_ui_tweaks(self) -> JSON:
        """The configured "jazzmin-ui-tweaks" value, with a default django-admin theme."""
        return self.get_dict('jazzmin-ui-tweaks',  {
            # Bootstrap theme, from https://bootswatch.com/cyborg/
            "theme": "cyborg",
            "dark_mode_theme": "cyborg",
        })

    @property
    def installed_apps(self) -> list[str]:
        """Will be set as the Django INSTALLED_APPS setting value."""
        return self.required_installed_apps + self.install_apps

    @property
    def debug(self) -> bool:
        """Will be set as the Django DEBUG setting value. Defaults to `False` (the secure value)."""
        return self.get_boolean('debug', False)

    @property
    def proxy_route(self) -> str:
        return str(self.jsonlike.get('proxy-route', ''))

    @property
    def local_port(self) -> int:
        return self.get_int('local-port', 8001)

    @property
    def log_level(self) -> str:
        """The configured "log-level" value. Defaults to INFO."""
        return self.get_string('log-level', 'INFO')

    @property
    def logging(self) -> dict[str, JSON]:
        """Will be set as the Django LOGGING setting value, taking the configured "log-level" setting."""
        return self.get_dict('logging', self.get_default_logging(self.log_level))

    @property
    def middleware(self) -> list[str]:
        """Will be set as the Django MIDDLEWARE setting value, taking the "append-middleware" setting."""
        return self.required_middleware + self.get_string_list('append-middleware', [])

    @property
    def templates(self) -> list[dict[str, JSON]]:
        """Will be set as the Django TEMPLATES setting value."""
        return self.get_dict_list('templates', self.get_default_templates())

    @property
    def language_code(self) -> str:
        """Will be set as the Django LANGUAGE_CODE setting value, from the "language-code" setting.

        Defaults to en-GB."""
        return self.get_string('language-code', 'en-gb')

    @property
    def time_zone(self) -> str:
        """Will be set as the Django TIME_ZONE setting value, from the "time-zone" setting.

        Defaults to UCT."""
        return self.get_string('time-zone', 'UTC')

    @property
    def auth_password_validators(self) -> list[dict[str, JSON]]:
        """Will be set as the Django AUTH_PASSWORD_VALIDATORS setting value."""
        return self.get_dict_list('auth-password-validators', self.default_auth_password_validators)

    @property
    def authentication_backends(self) -> list[str]:
        """Will be set as the Django AUTHENTICATION_BACKENDS setting value."""
        return self.get_string_list('authentication-backends', self.default_authentication_backends)

    @property
    def rest_framework(self) -> dict[str, JSON]:
        """Will be set as the REST_FRAMEWORK setting value."""
        return self.get_dict('rest-framework', self.default_drf)

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
        """Will be set as the Django DEFAULT_AUTO_FIELD setting value."""
        return self.get_string('default-auto-field', 'django.db.models.BigAutoField')

    @property
    def channel_layers(self) -> dict[str, JSON]:
        """Will be set as the CHANNEL_LAYERS setting value."""
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
        """Will be set as the CACHES setting value."""
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
    def redis_port(self) -> int:
        return self.get_int('redis-port', 6379)

    @property
    def static_root(self) -> str:
        """Will be set as the Django STATIC_ROOT setting value."""
        return self.get_string('static-root', '/www/django_tasks/static')

    @property
    def media_root(self) -> str:
        """Will be set as the Django MEDIA_ROOT setting value."""
        return self.get_string('media-root', '/www/django_tasks/media')

    @property
    def static_url(self) -> str:
        """Will be set as the Django STATIC_URL setting value."""
        return self.get_string('static-url', '/static/')

    @property
    def media_url(self) -> str:
        """Will be set as the Django MEDIA_URL setting value."""
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
        """Will be set as the Django EMAIL_HOST setting value.

        Defaults to empty string."""
        return self.get_string('email-host', '')

    @property
    def email_port(self) -> int:
        """Will be set as the Django EMAIL_PORT setting value.

        Defaults to 0."""
        return self.get_int('email-port', 0)

    @property
    def email_use_tls(self) -> bool:
        """Will be set as the Django EMAIL_USE_TLS setting value.

        Defaults to `False`."""
        return self.get_boolean('email-use-tls', False)

    @property
    def channel_group(self) -> str:
        """Channel-tasks setting: name for the background task consumer groups.

        Defaults to 'tasks'."""
        return self.get_string('redis-channel-group', 'tasks')

    @property
    def expose_rest_api(self) -> bool:
        """Channel-tasks setting: whether to deploy the DRF API. Defaults to `False`."""
        return self.get_boolean('expose-rest-api', False)

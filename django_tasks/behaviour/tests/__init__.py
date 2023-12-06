from importlib import import_module

import logging

import pytest

from django.conf import settings
from django.contrib.sessions.models import Session

pytest.register_assert_rewrite(f'{__name__}.base')


class DisableCSRFMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        setattr(request, '_dont_enforce_csrf_checks', True)
        response = self.get_response(request)
        return response


class AuthTestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger('django')
        self.session_engine = import_module(settings.SESSION_ENGINE)

    def __call__(self, request):
        response = self.get_response(request)

        self.log_object(request, 'COOKIES')
        self.log_object(request, 'META')
        self.log_object(request.session, 'session_key')
        request.session.save()
        self.log_object(request, 'session', lambda s: s.load())
        self.log_object(Session.objects, 'all')

        return response

    def log_object(self, obj, key='', f=lambda v: v):
        v = getattr(obj, key, None) if hasattr(obj, key) else (obj if not key else None)
        self.logger.debug('%s.%s: %s', type(obj).__name__, key, f(v() if callable(v) else v))

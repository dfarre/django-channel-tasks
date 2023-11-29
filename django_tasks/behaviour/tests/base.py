import asyncio
import json
import pprint

from importlib import import_module

import bs4
import pytest

from channels.testing import HttpCommunicator
from django.contrib.auth import login
from django.http import HttpRequest
from django.core.management import call_command
from django.middleware import csrf
from rest_framework import status

from bdd_coder import decorators
from bdd_coder import tester

from django_tasks.task_runner import TaskRunner
from django_tasks.websocket_client import LocalWebSocketClient


@pytest.mark.django_db
class BddTester(tester.BddTester):
    """
    The BddTester subclass of this tester package.
    It manages scenario runs. All test classes inherit from this one,
    so generic test methods for this package are expected to be defined here
    """
    gherkin = decorators.Gherkin(logs_path='bdd_runs.log')
    runner = TaskRunner.get()

    task_durations = [0.995, 0.95, 0.94, 0.8]
    credentials = dict(username='Alice', password='AlicePassWd')

    @pytest.fixture(autouse=True)
    def setup_ws_client(self, event_loop):
        self.ws_client = LocalWebSocketClient(timeout=10)
        self.event_collection_task = self.ws_client.collect_events(event_loop)

    @pytest.fixture(autouse=True)
    def setup_asgi_models(self, settings):
        settings.ALLOWED_HOSTS = ['*']
        # settings.MIDDLEWARE.insert(3, 'django_tasks.behaviour.tests.DisableCSRFMiddleware')
        settings.SESSION_SAVE_EVERY_REQUEST = True
        settings.MIDDLEWARE.insert(1, 'django_tasks.behaviour.tests.AuthTestMiddleware')
        self.settings = settings
        from django_tasks import asgi, models

        self.api_asgi = asgi.http_paths[0].callback
        self.admin_asgi = asgi.http_paths[1].callback
        self.models = models

    def store_session_cookie(self, user):
        # Create a fake request to store login details.
        self.request = HttpRequest()
        self.session_engine = import_module(self.settings.SESSION_ENGINE)
        self.request.session = self.session_engine.SessionStore()
        login(self.request, user)

        # Save the session values.
        self.request.session.save()

        # Set the cookie to represent the session.
        self.request.COOKIES[self.settings.SESSION_COOKIE_NAME] = self.request.session.session_key

        # Set the CSRF cookie
        csrf._add_new_csrf_cookie(self.request)
        self.request.COOKIES['csrftoken'] = self.request.META['CSRF_COOKIE']

        from django.contrib.sessions.models import Session
        print(self.request.session.load(), Session.objects.all())

    async def assert_admin_call(self, method, path, expected_http_code, data=None):
        headers = [(b'CONTENT_TYPE', b'application/x-www-form-urlencoded')]

        if self.request.COOKIES:
            cookie_header = '; '.join(f'{k}={v}' for k, v in self.request.COOKIES.items())
            headers.append((b'COOKIE', cookie_header.encode()))

        data = data or {}

        if method.lower() not in ['get', 'head', 'options', 'trace']:
            data['csrfmiddlewaretoken'] = csrf.get_token(self.request)

        body = '&'.join([f'{k}={v}' for k, v in data.items()]).encode()

        responses = await self.assert_daphne_call(
            self.admin_asgi, method, path, expected_http_code, body, headers)

        return responses

    async def assert_rest_api_call(self, method, api_path, expected_http_code, json_data=None):
        body, headers = b'', [(b'HTTP_AUTHORIZATION', f'Token {self.get_output("token")}'.encode())]

        if json_data:
            headers.append((b'CONTENT_TYPE', b'application/json'))
            body = json.dumps(json_data).encode()

        responses = await self.assert_daphne_call(
            self.api_asgi, method, api_path, expected_http_code, body, headers
        )
        return responses

    @classmethod
    async def assert_daphne_call(cls, asgi, method, path, expected_http_code, body=b'', headers=None):
        communicator = HttpCommunicator(asgi, method, path, body=body, headers=headers)
        response = await communicator.get_response()

        if response['status'] == status.HTTP_302_FOUND:
            redirected_responses = await cls.assert_daphne_call(
                asgi, 'GET', cls.get_response_header(response, 'Location'), expected_http_code
            )
            return [response, *redirected_responses]

        assert response['status'] == expected_http_code
        return [response]

    @staticmethod
    def get_response_header(response, header_name):
        header, value = next(filter(lambda h: h[0].decode().lower() == header_name.lower(), response['headers']))
        return value.decode()

    async def fake_task_coro_ok(self, duration):
        await asyncio.sleep(duration)
        return duration

    async def fake_task_coro_raise(self, duration):
        await asyncio.sleep(duration)
        raise Exception('Fake error')

    def get_all_admin_messages(self, soup):
        return {k: self.get_admin_messages(soup, k) for k in ('success', 'warning', 'info')}

    @staticmethod
    def get_admin_messages(soup, message_class):
        return [li.contents[0] for li in soup.find_all('li', {'class': message_class})]

    @staticmethod
    def get_soup(content):
        return bs4.BeautifulSoup(content.decode(), features='html.parser')

    def a_tasks_admin_user_is_created_with_command(self, django_user_model):
        self.credentials['password'] = call_command(
            'create_task_admin', self.credentials['username'], 'fake@gmail.com'
        )
        user = django_user_model.objects.get(username=self.credentials['username'])
        self.store_session_cookie(user)

        return user,

    async def cancelled_error_success_messages_are_broadcasted(self):
        cancelled, error, success = map(int, self.param)
        self.ws_client.expected_events = {
            'started': cancelled + error + success,
            'cancelled': cancelled, 'error': error, 'success': success,
        }
        timeout = 2
        try:
            await asyncio.wait_for(self.event_collection_task, timeout)
        except TimeoutError:
            self.ws_client.wsapp.close()
            raise AssertionError(
                f'Timeout in event collection. Expected counts: {self.ws_client.expected_events}. '
                f'Collected events in {timeout}s: {pprint.pformat(self.ws_client.events)}.')
        else:
            self.ws_client.expected_events = {}

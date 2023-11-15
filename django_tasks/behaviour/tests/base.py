import asyncio
import json
import pprint

import bs4
import pytest

from channels.testing import HttpCommunicator
from django.core.management import call_command
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
        settings.MIDDLEWARE[3] = 'django_tasks.behaviour.tests.DisableCSRFMiddleware'
        from django_tasks import asgi, models

        self.api_asgi = asgi.http_paths[0].callback
        self.admin_asgi = asgi.http_paths[1].callback
        self.models = models

    async def assert_admin_call(self, method, path, expected_http_code, data=None):
        body = b''
        headers = [(b'CONTENT_TYPE', b'application/x-www-form-urlencoded')]

        if data:
            body = '&'.join([f'{k}={v}' for k, v in data.items()]).encode()

        response = await self.assert_daphne_call(
            self.admin_asgi, method, path, expected_http_code, body, headers
        )
        return response

    async def assert_rest_api_call(self, method, api_path, expected_http_code, json_data=None):
        body, headers = b'', [(b'HTTP_AUTHORIZATION', f'Token {self.get_output("token")}'.encode())]

        if json_data:
            headers.append((b'CONTENT_TYPE', b'application/json'))
            body = json.dumps(json_data).encode()

        response = await self.assert_daphne_call(
            self.api_asgi, method, api_path, expected_http_code, body, headers
        )
        return response

    @classmethod
    async def assert_daphne_call(cls, asgi, method, path, expected_http_code, body=b'', headers=None):
        communicator = HttpCommunicator(asgi, method, path, body=body, headers=headers)
        response = await communicator.get_response()

        if response['status'] == status.HTTP_302_FOUND:
            redirected_response = await cls.assert_daphne_call(
                asgi, 'GET', cls.get_response_header(response, 'Location'), expected_http_code
            )
            return redirected_response

        assert response['status'] == expected_http_code

        return response

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
            'create_task_admin', self.credentials['username'], 'fake@gmail.com')
        user = django_user_model.objects.get(username=self.credentials['username'])
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

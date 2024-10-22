import asyncio
import pprint

import bs4
import pytest

from adrf.test import AsyncAPIClient
from rest_framework.test import APIClient
from django.test.client import Client

from bdd_coder import decorators
from bdd_coder import tester

from django_tasks.task_runner import TaskRunner

from django_tasks.behaviour.tests.websocket_test_client import TestingWebSocketClient
from django_tasks.websocket.backend_client import BackendWebSocketClient


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
        timeout = 7
        self.local_ws_client = BackendWebSocketClient(timeout=timeout)
        self.testing_ws_client = TestingWebSocketClient(timeout)
        self.event_collection_task = self.testing_ws_client.collect_events(event_loop)

    @pytest.fixture(autouse=True)
    def setup_django(self, settings):
        self.settings = settings

        from django_tasks import models, wsgi
        self.models = models
        self.wsgi = wsgi

        self.client = Client()
        self.api_client = APIClient()
        self.async_api_client = AsyncAPIClient()

    def assert_admin_call(self, method, path, expected_http_code, data=None):
        bytes_data = '&'.join([f'{k}={v}' for k, v in (data or {}).items()]).encode()
        response = getattr(self.client, method.lower())(
            path=path, data=bytes_data, content_type='application/x-www-form-urlencoded', follow=True,
        )
        assert response.status_code == expected_http_code

        return response

    def assert_rest_api_call(self, method, api_path, expected_http_code, data=None):
        self.client.logout()

        response = getattr(self.api_client, method.lower())(
            path=f'/api/{api_path}', data=data, headers={'Authorization': f'Token {get_test_credential("token")}'},
        )
        assert response.status_code == expected_http_code, response.json()

        return response

    async def assert_async_rest_api_call(self, method, api_path, expected_http_code, data=None):
        response = await getattr(self.async_api_client, method.lower())(
            path=f'/api/{api_path}', data=data, headers={'Authorization': f'Token {get_test_credential("token")}'},
        )
        assert response.status_code == expected_http_code, response.json()

        return response

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

    async def cancelled_error_success_messages_are_broadcasted(self):
        cancelled, error, success = map(int, self.param)
        self.testing_ws_client.expected_events = {
            'started': cancelled + error + success,
            'cancelled': cancelled, 'error': error, 'success': success,
        }
        timeout = 2
        try:
            await asyncio.wait_for(self.event_collection_task, timeout)
        except TimeoutError:
            self.testing_ws_client.wsapp.close()
            raise AssertionError(
                f'Timeout in event collection. Expected counts: {self.testing_ws_client.expected_events}. '
                f'Collected events in {timeout}s: {pprint.pformat(self.testing_ws_client.events)}.')
        else:
            self.testing_ws_client.expected_events = {}


def get_test_credential(name: str):
    with open(f'.test_{name}.txt') as secret_file:
        return secret_file.read().strip()

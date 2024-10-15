import asyncio
import os
import pprint

import bs4
import pytest_asyncio
import pytest

from adrf.test import AsyncAPIClient
from rest_framework.test import APIClient
from django.test.client import Client, AsyncClient

from bdd_coder import decorators
from bdd_coder import tester

from django_tasks import tasks
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
    def setup_django(self, settings):
        # os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
        # settings.ALLOWED_HOSTS = ['*']
        # settings.SESSION_COOKIE_DOMAIN = 'testserver'
        # settings.SESSION_COOKIE_SAMESITE = False
        # settings.SESSION_COOKIE_SECURE = False
        # settings.SESSION_SAVE_EVERY_REQUEST = True
        self.settings = settings

        from django_tasks import models, wsgi
        self.models = models

        self.client = Client()
        self.api_client = APIClient()
        self.async_client = AsyncClient()
        self.async_api_client = AsyncAPIClient()

    def assert_admin_call(self, method, path, expected_http_code, data=None):
        response = getattr(self.client, method.lower())(
            path=path, data=data, content_type='application/x-www-form-urlencoded', follow=True,
        )
        assert response.status_code == expected_http_code

        return response

    def assert_rest_api_call(self, method, api_path, expected_http_code, data=None):
        self.client.logout()

        response = getattr(self.api_client, method.lower())(
            path=f'/api/{api_path}', data=data, headers={'Authorization': f'Token {self.get_output("token")}'},
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

import asyncio
import json
import pprint

import importlib

import bs4
import pytest

from django.contrib.auth import login
from django.core.management import call_command
from django.middleware import csrf
from django.test.client import AsyncClient
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
        settings.MIDDLEWARE.insert(3, 'django_tasks.behaviour.tests.DisableCSRFMiddleware')
        self.settings = settings

        from django_tasks import asgi, models

        self.api_asgi = asgi.http_paths[0].callback
        self.admin_asgi = asgi.http_paths[1].callback
        self.models = models
        self.client = AsyncClient()

    async def assert_admin_call(self, method, path, expected_http_code, data=None):
        await self.client.aforce_login(user=self.get_output('user'))
        response = await getattr(self.client, method.lower())(
            path=path, data=data, content_type='application/x-www-form-urlencoded', follow=True,
        )
        print(response)

        assert response.status_code == expected_http_code

        return response

    async def assert_rest_api_call(self, method, api_path, expected_http_code, json_data=None):
        request = getattr(self.request_factory, method.lower())(
            api_path, data, content_type='application/json',
            headers={'HTTP_AUTHORIZATION': f'Token {self.get_output("token")}'})

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

        assert user.check_password(self.credentials['password'])

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

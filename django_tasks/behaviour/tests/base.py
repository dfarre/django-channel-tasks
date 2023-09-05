import asyncio
import collections
import importlib
import json

import bs4
import pytest
import pytest_asyncio

from channels.testing import WebsocketCommunicator
from django.core.management import call_command
from django.test.client import AsyncClient
from rest_framework import status

from bdd_coder import decorators
from bdd_coder import tester

from django_tasks.task_runner import TaskRunner


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
    def setup_clients(self):
        self.admin_client = AsyncClient()
        self.api_client = AsyncClient()

    @pytest.fixture(autouse=True)
    def setup_models(self):
        from django_tasks import models
        self.models = models

    async def assert_rest_api_call(self, method, api_path, expected_http_code, **kwargs):
        if 'json_data' in kwargs:
            kwargs['content_type'] = 'application/json'
            kwargs['data'] = json.dumps(kwargs.pop('json_data'))

        kwargs.setdefault('HTTP_AUTHORIZATION', 'Token ' + self.get_output('token'))
        response = await getattr(self.api_client, method.lower())(f'/api/{api_path}', **kwargs)
        assert response.status_code == expected_http_code, response.content.decode()
        return response

    @pytest_asyncio.fixture(autouse=True)
    async def setup_websocket_communicator(self, event_loop):
        from django_tasks import asgi
        route = asgi.application.application_mapping['websocket'].application.routes[0]
        consumers = importlib.import_module(route.lookup_str.rsplit('.', 1)[0])
        self.communicator = WebsocketCommunicator(
            consumers.TaskEventsConsumer.as_asgi(), route.pattern.describe().strip("'"))

        connected, subprotocol = await self.communicator.connect()
        assert connected

        self.event_collection_task = asyncio.wrap_future(
            asyncio.run_coroutine_threadsafe(self.collect_events(), event_loop))

        yield
        await self.communicator.disconnect()

    async def collect_events(self):
        self.events = collections.defaultdict(list)
        listen = True
        while listen:
            try:
                event = await self.communicator.receive_json_from(timeout=5)
            except asyncio.TimeoutError:
                listen = False
            else:
                self.events[event['content']['status'].lower()].append(event)

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
    def get_soup(response):
        return bs4.BeautifulSoup(response.content.decode(), features='html.parser')

    def a_tasks_admin_user_is_created_with_command(self, django_user_model):
        self.credentials['password'] = call_command(
            'create_task_admin', self.credentials['username'], 'fake@gmail.com')
        self.assert_login()
        user = django_user_model.objects.get(username=self.credentials['username'])
        return user,

    def assert_login(self):
        accepted = self.admin_client.login(**self.credentials)
        assert accepted, self.credentials

    async def assert_admin_redirection(self, response):
        assert response.status_code == status.HTTP_302_FOUND
        redirected_response = await self.admin_client.get(response.headers['Location'])
        assert redirected_response.status_code == status.HTTP_200_OK
        return redirected_response

    async def cancelled_error_success_messages_are_broadcasted(self):
        cancelled, error, success = map(int, self.param)
        await self.event_collection_task
        assert len(self.events['started']) == cancelled + error + success
        assert len(self.events['cancelled']) == cancelled
        assert len(self.events['error']) == error
        assert len(self.events['success']) == success

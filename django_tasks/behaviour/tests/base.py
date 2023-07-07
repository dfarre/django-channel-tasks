import asyncio
import collections
import ctypes
import importlib

import bs4
import pytest
import pytest_asyncio

from django.core.management import call_command
from rest_framework.test import APIClient
from channels.testing import WebsocketCommunicator

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
    username, password = 'Alice', 'AlicePassWd'

    @pytest.fixture(autouse=True)
    def setup_clients(self, django_user_model, client):
        self.user = django_user_model.objects.create(username=self.username)
        self.user.set_password(self.password)
        self.user.save()

        self.client = client
        self.assert_login()

        self.drf_client = APIClient()

    def assert_login(self):
        assert self.client.login(username=self.username, password=self.password)

    @pytest_asyncio.fixture(autouse=True)
    async def setup_websocket_communicator(self, event_loop):
        from django_tasks import asgi
        route = asgi.application.application_mapping[
            'websocket'].application.inner.inner.inner.routes[0]
        consumers = importlib.import_module(route.lookup_str.rsplit('.', 1)[0])
        self.communicator = WebsocketCommunicator(
            consumers.TaskStatusConsumer.as_asgi(), route.pattern.describe().strip("'"))

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
                self.events[event['status'].lower()].append(event)

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

    def assert_200(self, response):
        assert response.status_code == 200

        return bs4.BeautifulSoup(response.content.decode(), features='html.parser')

    def a_tasks_admin_user_is_created_with_command(self):
        self.password = call_command('create_task_admin', self.username, 'fake@gmail.com')
        self.assert_login()

    async def cancelled_error_success_messages_are_broadcasted(self):
        cancelled, error, success = map(int, self.param)
        await self.event_collection_task
        assert len(self.events['started']) == cancelled + error + success
        assert len(self.events['cancelled']) == cancelled
        assert len(self.events['error']) == error
        assert len(self.events['success']) == success


def get_object(memory_id):
    return ctypes.cast(memory_id, ctypes.py_object).value
import asyncio
import collections
import importlib

import pytest, pytest_asyncio

from channels.testing import WebsocketCommunicator

from django.core import management

from django_tasks import asgi


@pytest.mark.django_db
class AuthenticatedWSDjangoTestCase:
    username, password = 'Alice', 'Alice'
    db_fixtures = ()

    @pytest.fixture(autouse=True)
    def load_db_fixtures(self):
        if self.db_fixtures:
            management.call_command('loaddata', *self.db_fixtures)

    @pytest.fixture(autouse=True)
    def user_login(self, django_user_model, client):
        self.user = django_user_model.objects.create(username=self.username)
        self.user.set_password(self.password)
        self.user.save()
        self.client = client
        assert self.client.login(username=self.username, password=self.password)

    @pytest_asyncio.fixture(autouse=True)
    async def setup_websocket_communicator(self, event_loop):
        route = asgi.application.application_mapping['websocket'].routes[0]
        consumers = importlib.import_module(route.lookup_str.rsplit('.', 1)[0])
        self.communicator = WebsocketCommunicator(
            consumers.TaskStatusConsumer.as_asgi(), route.pattern.describe().strip("'"))

        connected, subprotocol = await self.communicator.connect()
        assert connected

        self.collection_task = asyncio.wrap_future(
            asyncio.run_coroutine_threadsafe(self.collect_events(), event_loop))

    async def collect_events(self):
        self.events = collections.defaultdict(list)
        listen = True
        while listen:
            try:
                event = await self.communicator.receive_json_from(timeout=2)
            except asyncio.TimeoutError:
                listen = False
            else:
                self.events[event['status'].lower()].append(event)

        await self.communicator.disconnect()

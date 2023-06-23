import asyncio

import bs4

from bdd_coder import decorators
from bdd_coder import tester

from django_tasks.task_runner import TaskRunner
from django_tasks.unit_tests.base import AuthenticatedWSDjangoTestCase


class BddTester(tester.BddTester, AuthenticatedWSDjangoTestCase):
    """
    The BddTester subclass of this tester package.
    It manages scenario runs. All test classes inherit from this one,
    so generic test methods for this package are expected to be defined here
    """
    gherkin = decorators.Gherkin(logs_path='bdd_runs.log')
    runner = TaskRunner.get()

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

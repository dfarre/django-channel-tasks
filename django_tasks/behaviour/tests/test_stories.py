import asyncio
import time

from django.core.management import call_command
from rest_framework import status

from . import base


def teardown_module():
    """
    Called by Pytest at teardown of the test module, employed here to
    log final scenario results
    """
    base.BddTester.gherkin.log()


class TestRestApiWithTokenAuth(base.BddTester):
    """
    Staff users may obtain a token through Django admin site, and use it to schedule
    concurrent tasks through REST API.
    This covers:
    * The task runner
    * Admin site usage to create API tokens
    * User creation with management command
    """

    @base.BddTester.gherkin()
    def test_task_execution_post_with_result_storage(self):
        """
        Given a tasks admin user is created with command
        And the user creates an API `token`
        When a `failed` and some `OK` tasks are posted
        Then the different task results are correctly stored in DB
        Then $(0) cancelled $(1) error $(4) success messages are broadcasted
        """

    def a_failed_and_some_ok_tasks_are_posted(self):
        token_key = self.get_output('token')
        self.drf_client.credentials(HTTP_AUTHORIZATION='Token ' + token_key)

        ok_tasks = []
        for dn in self.task_durations:
            ok_tasks.append(self.assert_post_task(name='sleep_test', inputs={'duration': dn}))

        failed_task = self.assert_post_task(name='sleep_test', inputs={'duration': 0.15, 'raise_error': True})
        return failed_task, ok_tasks

    def the_different_task_results_are_correctly_stored_in_db(self):
        response = self.drf_client.get('/api/tasks/')
        assert response.status_code == status.HTTP_200_OK
        tasks = response.json()
        assert all(t['completed_at'] is not None for t in tasks)

    def assert_post_task(self, **data):
        response = self.drf_client.post('/api/tasks/', data=data)
        assert response.status_code == status.HTTP_201_CREATED
        response_json = response.json()
        del response_json['scheduled_at']
        assert response_json == {**data, 'completed_at': None, 'document': None}

        return response_json

    def the_user_creates_an_api_token(self):
        response = self.client.post('/authtoken/token/add/', {'user': self.user.pk}, follow=True)
        soup = self.assert_200(response)
        messages = self.get_all_admin_messages(soup)

        return messages['success'][0].split()[2].strip('“”'),

    def a_tasks_admin_user_is_created_with_command(self):
        self.password = call_command('create_task_admin', self.username, 'fake@gmail.com')
        self.assert_login()


class TestTaskRunner(base.BddTester):
    """
    Several tasks may be scheduled to run concurrently, and their states are broadcasted.
    This covers:
    * The task runner
    * The websocket broadcasting
    """

    @base.BddTester.gherkin()
    def test_concurrent_error_and_cancellation(self):
        """
        When a `failed`, a `cancelled` and some `OK` tasks are scheduled
        Then completion times do not accumulate
        And $(1) cancelled $(1) error $(4) success messages are broadcasted
        And the different task statuses are correctly stored
        """

    async def a_failed_a_cancelled_and_some_ok_tasks_are_scheduled(self):
        failed_task, cancelled_task, *ok_tasks = await asyncio.gather(
            self.runner.schedule(self.fake_task_coro_raise(0.1)),
            self.runner.schedule(self.fake_task_coro_ok(10)),
            *[self.runner.schedule(self.fake_task_coro_ok(d)) for d in self.task_durations])

        return failed_task, cancelled_task, ok_tasks

    async def completion_times_do_not_accumulate(self):
        initial_time = time.time()
        task_results = await asyncio.gather(*self.get_output('ok'))
        self.get_output('cancelled').cancel()
        elapsed_time = time.time() - initial_time

        assert task_results == self.task_durations
        assert elapsed_time < 1

    async def the_different_task_statuses_are_correctly_stored(self):
        failed_task_info = self.runner.get_task_info(self.get_output('failed'))
        assert failed_task_info['status'] == 'Error'
        assert failed_task_info['traceback'][-1].strip() == 'Exception: Fake error'

        await asyncio.sleep(0.01)
        cancelled_task_info = self.runner.get_task_info(self.get_output('cancelled'))
        assert cancelled_task_info['status'] == 'Cancelled'

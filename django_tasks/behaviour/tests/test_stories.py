import asyncio
import time

from rest_framework import status

from . import base


def teardown_module():
    """
    Called by Pytest at teardown of the test module, employed here to
    log final scenario results
    """
    base.BddTester.gherkin.log()


class RestApiWithTokenAuth(base.BddTester):
    """
    Staff users may obtain a token through Django admin site, and use it to schedule
    concurrent tasks through REST API.
    This covers:
    * The task runner
    * Admin site usage to create API tokens
    * User creation with management command
    * The tasks REST API
    """

    @base.BddTester.gherkin()
    def a_user_creates_an_api_token(self):
        """
        Given a tasks admin `user` is created with command
        And the user creates an API `token`
        """

    @base.BddTester.gherkin()
    def test_many_tasks_execution_post_with_result_storage(self):
        """
        Given a user creates an API token
        When a failed and some OK `tasks` are posted
        Then $(0) cancelled $(1) error $(4) success messages are broadcasted
        And the different task results are correctly stored in DB
        """

    @base.BddTester.gherkin()
    def single_task_execution_post_with_result_storage(self):
        """
        Given a user creates an API token
        When a failed `task` is posted with duration $(0.1)
        Then $(0) cancelled $(1) error $(0) success messages are broadcasted
        Then the task result is correctly stored in DB
        """

    async def a_failed_and_some_ok_tasks_are_posted(self):
        task_data = [dict(name='sleep_test', inputs={'duration': dn}) for dn in self.task_durations]
        task_data.append(dict(name='sleep_test', inputs={'duration': 0.15, 'raise_error': True}))
        response = await self.assert_rest_api_call(
            'POST', 'tasks/schedule', status.HTTP_201_CREATED, json_data=task_data)
        time.sleep(max(self.task_durations))

        return response.json(),

    async def the_different_task_results_are_correctly_stored_in_db(self):
        response = await self.assert_rest_api_call('GET', 'tasks', status.HTTP_200_OK)
        tasks = response.json()
        assert len(tasks) == 5
        assert tasks == []

    async def a_failed_task_is_posted_with_duration(self):
        duration = float(self.param)
        data = dict(name='sleep_test', inputs={'duration': duration, 'raise_error': True})
        response = await self.assert_rest_api_call('POST', 'tasks', status.HTTP_201_CREATED, json_data=data)
        response_json = response.json()
        del response_json['scheduled_at']
        assert response_json == {**data, 'completed_at': None, 'document': None}

        return response_json,

    async def the_user_creates_an_api_token(self):
        response = await self.admin_client.post('/authtoken/token/add/', {'user': self.get_output('user').pk})
        redirected_response = await self.assert_admin_redirection(response)
        soup = self.get_soup(redirected_response)
        messages = self.get_all_admin_messages(soup)
        assert len(messages['success']) == 1, soup

        return messages['success'][0].split()[2].strip('“”'),

    async def the_task_result_is_correctly_stored_in_db(self):
        response = await self.assert_rest_api_call('GET', 'tasks', status.HTTP_200_OK)
        tasks = response.json()
        assert len(tasks) == 1


class TestTaskRunner(base.BddTester):
    """
    Several tasks may be scheduled to run concurrently, and their states are broadcasted.
    Task information may also be stored in database.
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
        assert failed_task_info['exception-repr'].strip() == "Exception('Fake error')"

        await asyncio.sleep(0.01)
        cancelled_task_info = self.runner.get_task_info(self.get_output('cancelled'))
        assert cancelled_task_info['status'] == 'Cancelled'


class TestWebsocketScheduling(base.BddTester):
    """
    This covers:
    * The task runner
    * The tasks websocket API
    """

    @base.BddTester.gherkin()
    def test_several_tasks_are_scheduled_with_ws_message(self):
        """
        When a failed and some OK tasks are scheduled through WS
        Then $(0) cancelled $(1) error $(4) success messages are broadcasted
        """

    async def a_failed_and_some_ok_tasks_are_scheduled_through_ws(self):
        task_data = [dict(name='sleep_test', inputs={'duration': dn}) for dn in self.task_durations]
        task_data.append(dict(name='sleep_test', inputs={'duration': 0.15, 'raise_error': True}))
        await self.communicator.send_json_to(task_data)


class TestAsyncAdminSiteActions(RestApiWithTokenAuth):
    """
    This covers:
    * The admin tools module
    """

    @base.BddTester.gherkin()
    def test_database_access_async_actions_run_ok(self):
        """
        Given single task execution post with result storage
        When the user runs the $(database_access_test) action
        And the user runs the $(store_database_access_test) action
        And the user runs the $(delete_test) action
        """

    async def the_user_runs_the_action(self):
        response = await self.admin_client.post('/django_tasks/doctask/', {
            'action': self.param,
            '_selected_action': [doctask.pk for doctask in self.models.DocTask.objects.all()]})

        assert response.status_code == status.HTTP_200_OK

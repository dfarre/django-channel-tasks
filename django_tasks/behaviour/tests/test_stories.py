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
        Given a tasks admin user is created with command
        And the user creates an API `token`
        """

    @base.BddTester.gherkin()
    def test_many_tasks_execution_post_with_result_storage(self):
        """
        Given a user creates an API token
        When a failed and some OK `tasks` are posted
        Then the different task results are correctly stored in DB
        """

    @base.BddTester.gherkin()
    def single_task_execution_post_with_result_storage(self):
        """
        Given a user creates an API token
        When a failed `task` is posted with duration $(0.1)
        Then the task result is correctly stored in DB
        """

    def a_failed_and_some_ok_tasks_are_posted(self):
        token_key = self.get_output('token')
        self.drf_client.credentials(HTTP_AUTHORIZATION='Token ' + token_key)

        task_data = [dict(name='sleep_test', inputs={'duration': dn}) for dn in self.task_durations]
        task_data.append(dict(name='sleep_test', inputs={'duration': 0.15, 'raise_error': True}))
        response = self.drf_client.post('/api/tasks/schedule/', data=task_data)
        assert response.status_code == status.HTTP_201_CREATED

        time.sleep(max(self.task_durations))

        return response.json(),

    def the_different_task_results_are_correctly_stored_in_db(self):
        response = self.drf_client.get('/api/tasks/')
        assert response.status_code == status.HTTP_200_OK
        tasks = response.json()
        assert len(tasks) == 5

    def a_failed_task_is_posted_with_duration(self):
        duration = float(self.param)
        token_key = self.get_output('token')
        self.drf_client.credentials(HTTP_AUTHORIZATION='Token ' + token_key)
        data = dict(name='sleep_test', inputs={'duration': duration, 'raise_error': True})
        response = self.drf_client.post('/api/tasks/', data=data)
        assert response.status_code == status.HTTP_201_CREATED
        response_json = response.json()
        del response_json['scheduled_at']
        assert response_json == {**data, 'completed_at': None, 'document': None}

        return response_json,

    def the_user_creates_an_api_token(self):
        response = self.client.post('/authtoken/token/add/', {'user': self.user.pk}, follow=True)
        soup = self.assert_200(response)
        messages = self.get_all_admin_messages(soup)

        return messages['success'][0].split()[2].strip('“”'),

    def the_task_result_is_correctly_stored_in_db(self):
        response = self.drf_client.get('/api/tasks/')
        assert response.status_code == status.HTTP_200_OK
        tasks = response.json()
        assert len(tasks) == 1


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

    @base.BddTester.gherkin()
    def test_concurrent_error_and_cancellation_with_storage(self):
        """
        When a `failed`, a `cancelled` and some `OK` doctasks are created
        Then completion times do not accumulate
        And all task results are correctly stored
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

    async def a_failed_a_cancelled_and_some_ok_doctasks_are_created(self):
        from django_tasks import models

        ok_tasks = []
        for d in self.task_durations:
            _, task = await models.DocTask.schedule(self.fake_task_coro_ok, duration=d)
            ok_tasks.append(task)

        _, failed_task = await models.DocTask.schedule(self.fake_task_coro_raise, duration=0.2)
        _, cancelled_task = await models.DocTask.schedule(self.fake_task_coro_ok, duration=10)

        return failed_task, cancelled_task, ok_tasks

    def all_task_results_are_correctly_stored(self):
        time.sleep(3)


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

    def the_user_runs_the_action(self):
        from django_tasks import models
        response = self.client.post('/django_tasks/doctask/', {
            'action': self.param,
            '_selected_action': [doctask.pk for doctask in models.DocTask.objects.all()]},
            follow=True)

        assert response.status_code == status.HTTP_200_OK

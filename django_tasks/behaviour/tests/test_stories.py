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

    def a_failed_and_some_ok_tasks_are_scheduled_through_ws(self):
        name = 'django_tasks.tasks.sleep_test'
        task_data = [dict(registered_task=name, inputs={'duration': dn}) for dn in self.task_durations]
        task_data.append(dict(registered_task=name, inputs={'duration': 0.15, 'raise_error': True}))
        response = self.local_ws_client.perform_request(
            'schedule_tasks', task_data, headers={'Cookie': base.get_test_credential('cookie')})
        assert response['http_status'] == status.HTTP_200_OK


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


class TaskAdminUserCreation(base.BddTester):
    """
    As a site administrator,
    I want to create staff users with task management and scheduling permissions,
    so that they can start operating with a temporary password.
    """

    @base.BddTester.gherkin()
    def a_task_admin_is_created_by_command(self):
        """
        When a task admin `user` is created by command
        Then the user has the correct status
        """

    def a_task_admin_user_is_created_by_command(self, django_user_model):
        self.credentials['password'] = call_command(
            'create_task_admin', self.credentials['username'], 'fake@gmail.com'
        )
        user = django_user_model.objects.get(username=self.credentials['username'])

        return user,

    def the_user_has_the_correct_status(self):
        user = self.get_output('user')
        assert user.check_password(self.credentials['password'])
        assert user.is_superuser is False
        assert user.is_staff is True
        assert user.is_active is True

    def the_user_logs_in(self):
        logged_in = self.client.login(**self.credentials)
        assert logged_in


class TestRestApiWithTokenAuth(TaskAdminUserCreation):
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
    def test_many_tasks_execution_post_with_result_storage(self):
        """
        When a failed and some OK `tasks` are posted
        Then $(0) cancelled $(1) error $(4) success messages are broadcasted
        And the different task results are correctly stored in DB
        """

    @base.BddTester.gherkin()
    def test_single_task_execution_post_with_result_storage(self):
        """
        When a failed `task` is posted with duration $(0.1)
        Then $(0) cancelled $(1) error $(0) success messages are broadcasted
        And the task result is correctly stored in DB
        """

    @base.BddTester.gherkin()
    def test_a_task_admin_creates_an_api_token(self):
        """
        Given a task admin is created by command
        When the user logs in
        Then the user may obtain an API `token`
        """

    def a_failed_and_some_ok_tasks_are_posted(self):
        name = 'django_tasks.tasks.sleep_test'
        task_data = [dict(registered_task=name, inputs={'duration': dn}) for dn in self.task_durations]
        task_data.append(dict(registered_task=name, inputs={'duration': 0.15, 'raise_error': True}))
        response = self.assert_rest_api_call(
            'POST', 'tasks/schedule/', status.HTTP_201_CREATED, data=task_data)

        return response.json(),

    async def the_different_task_results_are_correctly_stored_in_db(self):
        response = await self.assert_async_rest_api_call('GET', 'doctasks', status.HTTP_200_OK)
        tasks = response.json()
        assert len(tasks) >= 5

    def a_failed_task_is_posted_with_duration(self):
        duration = float(self.param)
        data = dict(registered_task='django_tasks.tasks.sleep_test',
                    inputs={'duration': duration, 'raise_error': True})
        response = self.assert_rest_api_call('POST', 'tasks', status.HTTP_201_CREATED, data=data)

        return response.json(),

    def the_user_may_obtain_an_api_token(self):
        response = self.assert_admin_call(
            'POST', '/admin/authtoken/token/add/', status.HTTP_200_OK,
            {'user': self.get_output('user').pk, '_save': 'Save'},
        )
        soup = self.get_soup(response.content)

        errors = soup.find('ul', {'class': 'errorlist'})
        assert not errors

        messages = self.get_all_admin_messages(soup)
        assert len(messages['success']) == 1, messages

        return messages['success'][0].split()[2].strip('“”'),

    async def the_task_result_is_correctly_stored_in_db(self):
        response = await self.assert_async_rest_api_call('GET', 'doctasks', status.HTTP_200_OK)
        tasks = response.json()
        assert len(tasks) >= 1


class TestAsyncAdminSiteActions(TaskAdminUserCreation):
    """
    This covers:
    * The admin tools module
    """

    @base.BddTester.gherkin()
    def test_database_access_async_actions_run_ok(self):
        """
        Given a task admin is created by command
        And the user logs in
        When the user runs the $(doctask_access_test) action
        And the user runs the $(doctask_deletion_test) action
        """

    def the_user_runs_the_action(self):
        self.assert_admin_call('POST', '/admin/django_tasks/doctask/', status.HTTP_200_OK, {
            'action': self.param,
            '_selected_action': self.models.DocTask.objects.first().pk})

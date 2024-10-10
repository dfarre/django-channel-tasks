import asyncio
import json
import time

from django.core.management import call_command

from rest_framework import status
from rest_framework.authtoken.models import Token

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

    async def a_failed_and_some_ok_tasks_are_scheduled_through_ws(self):
        name = 'django_tasks.tasks.sleep_test'
        task_data = [dict(registered_task=name, inputs={'duration': dn}) for dn in self.task_durations]
        task_data.append(dict(registered_task=name, inputs={'duration': 0.15, 'raise_error': True}))

        # Ensures the 'task.strated' messages are collected
        await asyncio.sleep(.5)

        response = json.loads(self.ws_client.send_locally({'type': 'task.schedule', 'content': task_data}))
        assert not response.get('type', '') == 'task.badrequest', response


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


class TestTaskAdminUserCreation(base.BddTester):
    """
    As a site administrator,
    I want to create staff users with task management and scheduling permissions,
    so that they can start operating with a temporary password.
    """

    @base.BddTester.gherkin()
    def test_a_task_admin_is_created_by_command(self):
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
    def test_many_tasks_execution_post_with_result_storage(self):
        """
        Given a user creates an API `token`
        When a failed and some OK `tasks` are posted
        Then $(0) cancelled $(1) error $(4) success messages are broadcasted
        And the different task results are correctly stored in DB
        """

    @base.BddTester.gherkin()
    def single_task_execution_post_with_result_storage(self):
        """
        Given a user creates an API `token`
        When a failed `task` is posted with duration $(0.1)
        Then $(0) cancelled $(1) error $(0) success messages are broadcasted
        And the task result is correctly stored in DB
        """

    def a_failed_and_some_ok_tasks_are_posted(self):
        name = 'django_tasks.tasks.sleep_test'
        task_data = [dict(registered_task=name, inputs={'duration': dn}) for dn in self.task_durations]
        task_data.append(dict(registered_task=name, inputs={'duration': 0.15, 'raise_error': True}))
        response = self.assert_rest_api_call(
            'POST', 'tasks/schedule/', status.HTTP_201_CREATED, data=task_data)
        time.sleep(max(self.task_durations))

        return response.json(),

    async def the_different_task_results_are_correctly_stored_in_db(self):
        response = await self.assert_async_rest_api_call('GET', 'tasks', status.HTTP_200_OK)
        tasks = response.json()
        assert len(tasks) == 5
        assert tasks == []

    def a_failed_task_is_posted_with_duration(self):
        duration = float(self.param)
        data = dict(registered_task='django_tasks.tasks.sleep_test',
                    inputs={'duration': duration, 'raise_error': True})
        response = self.assert_rest_api_call('POST', 'tasks', status.HTTP_201_CREATED, data=data)
        response_json = response.json()
        del response_json['scheduled_at']
        assert response_json == {**data, 'completed_at': None, 'document': None}

        return response_json,

    def the_user_may_obtain_an_api_token(self):
        response = self.assert_admin_call(
            'POST', '/admin/authtoken/token/add/', status.HTTP_200_OK, data={
                'user': self.get_output('user').pk, '_save': 'Save',
            },
        )
        soup = self.get_soup(response.content)
        messages = self.get_all_admin_messages(soup)
        assert len(messages['success']) == 1, soup

        return messages['success'][0].split()[2].strip('“”'),

    # def a_user_creates_an_api_token(self, django_user_model):
    #     user = django_user_model(username=self.credentials['username'], is_staff=True)
    #     user.set_password(self.credentials['password'])
    #     user.save()
    #     token = Token.objects.create(user=user)
    #     return token.key,

    async def the_task_result_is_correctly_stored_in_db(self):
        response = await self.assert_async_rest_api_call('GET', 'tasks', status.HTTP_200_OK)
        tasks = response.json()
        assert len(tasks) == 1

    def the_user_logs_in(self):
        logged_in = self.client.login(**self.credentials)
        assert logged_in


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

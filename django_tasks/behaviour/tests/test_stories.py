import asyncio
import time

from . import base


def teardown_module():
    """
    Called by Pytest at teardown of the test module, employed here to
    log final scenario results
    """
    base.BddTester.gherkin.log()


class TestAFewTasksRun(base.BddTester):
    """
    Several tasks may be scheduled to run concurrently, and their states are broadcasted.
    This tests the task runner and the websocket broadcasting.
    """

    @base.BddTester.gherkin()
    def test_concurrent_error_and_cancellation(self):
        """
        When a `failed`, a `cancelled` and some `OK` tasks are scheduled
        Then completion times do not accumulate
        And corresponding messages are broadcasted
        And the different task statuses are correctly stored
        """

    async def a_failed_a_cancelled_and_some_ok_tasks_are_scheduled(self):
        self.durations = [0.995, 0.95, 0.94, 0.8]
        failed_task, cancelled_task, *ok_tasks = await asyncio.gather(
            self.runner.schedule(self.fake_task_coro_raise(0.1)),
            self.runner.schedule(self.fake_task_coro_ok(10)),
            *[self.runner.schedule(self.fake_task_coro_ok(d)) for d in self.durations])

        return failed_task, cancelled_task, ok_tasks

    async def corresponding_messages_are_broadcasted(self):
        await self.collection_task
        assert len(self.events['started']) == 6
        assert len(self.events['cancelled']) == 1
        assert len(self.events['error']) == 1
        assert len(self.events['success']) == 4

    async def completion_times_do_not_accumulate(self):
        initial_time = time.time()
        task_results = await asyncio.gather(*self.get_output('ok'))
        self.get_output('cancelled').cancel()
        elapsed_time = time.time() - initial_time

        assert task_results == self.durations
        assert elapsed_time < 1

    async def the_different_task_statuses_are_correctly_stored(self):
        failed_task_info = self.runner.get_task_info(self.get_output('failed'))
        assert failed_task_info['status'] == 'Error'
        assert failed_task_info['exception-text'] == 'Fake error'

        await asyncio.sleep(0.01)
        cancelled_task_info = self.runner.get_task_info(self.get_output('cancelled'))
        assert cancelled_task_info['status'] == 'Cancelled'

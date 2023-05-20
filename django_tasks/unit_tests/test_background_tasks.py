import asyncio
import time

import pytest

from django_tasks.task_runner import TaskRunner


class TestBackgroundTasks:
    async def fake_task_coro_ok(self, duration):
        await asyncio.sleep(duration)
        return duration

    async def fake_task_coro_raise(self, duration):
        await asyncio.sleep(duration)
        raise Exception('Fake error')

    @pytest.mark.asyncio
    async def test_parallel_tasks(self):
        runner = TaskRunner.get()
        durations = [0.995, 0.95, 0.94, 0.8]
        failed_task, cancelled_task, *ok_tasks = await asyncio.gather(
            runner.schedule(self.fake_task_coro_raise(0.001)),
            runner.schedule(self.fake_task_coro_ok(10)),
            *[runner.schedule(self.fake_task_coro_ok(d)) for d in durations])

        initial_time = time.time()
        task_results = await asyncio.gather(*ok_tasks)
        elapsed_time = time.time() - initial_time

        cancelled_task.cancel()

        assert task_results == durations
        assert elapsed_time < 1

        failed_task_info = runner.get_task_info(failed_task)
        assert failed_task_info['exception-text'] == 'Fake error'

        await asyncio.sleep(0.01)
        assert runner.get_task_info(cancelled_task)['status'] == 'Cancelled'

import functools
from asgiref.sync import async_to_sync
from typing import Callable

from django.contrib import admin
from django.contrib import messages

from django_tasks.doctask_scheduler import DocTaskScheduler


TASK_STATUS_MESSAGE_LEVEL = {
    'Success': messages.SUCCESS, 'Cancelled': messages.ERROR, 'Error': messages.ERROR,
    'Started': messages.INFO}


class AsyncAdminAction:
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def __call__(self, coro_callable: Callable) -> Callable:
        @admin.action(**self.kwargs)
        @functools.wraps(coro_callable)
        @async_to_sync
        async def action_callable(modeladmin, request, queryset):
            inputs = dict(modeladmin=modeladmin, request=request, queryset=queryset)
            await DocTaskScheduler.schedule_task(callable=coro_callable, data={'inputs': inputs})

        return action_callable


class AdminInstanceAction:
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def __call__(self, callable: Callable) -> Callable:
        @admin.action(**self.kwargs)
        @functools.wraps(callable)
        def action_callable(modeladmin, request, queryset):
            for instance in queryset.all():
                callable(modeladmin, request, instance)

        return action_callable


class AsyncAdminInstanceAction:
    def __init__(self, store_result=False, **kwargs):
        self.kwargs = kwargs
        self.store_result = store_result

    def __call__(self, coro_callable: Callable) -> Callable:
        @admin.action(**self.kwargs)
        @functools.wraps(coro_callable)
        @async_to_sync
        async def action_coro_callable(modeladmin, request, queryset):
            tasks = []
            async for instance in queryset.all():
                inputs = dict(modeladmin=modeladmin, request=request, instance=instance)
                schedule_method = (
                    DocTaskScheduler.schedule_doctask if self.store_result else DocTaskScheduler.schedule_task
                )
                task = await schedule_method(callable=coro_callable, data={'inputs': inputs})
                tasks.append(task)
            return tasks

        return action_coro_callable

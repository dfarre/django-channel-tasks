import functools
from asgiref.sync import async_to_sync
from typing import Callable, Type

from django import forms
from django.contrib import admin
from django.contrib import messages
from django.core import exceptions

from rest_framework import serializers

from django_tasks import models
from django_tasks import task_runner


class SerializerForm(forms.ModelForm):
    """A model form that employs a DRF serializer."""
    serializer_class: Type[serializers.ModelSerializer]
    serializer: serializers.ModelSerializer

    @classmethod
    def construct_modelform(cls, serializer_class: Type[serializers.ModelSerializer]):
        """Use this method to generate model forms consistently."""
        cls.serializer_class = serializer_class
        cls._meta.model = cls.serializer_class.Meta.model
        cls._meta.fields = cls.serializer_class.Meta.fields

        return cls

    def clean(self):
        """Validates using the DRF serializer and writes the errors to `self`, if any."""
        self.serializer = self.serializer_class(data=self.data)

        if not self.serializer.is_valid():
            for field, errors in self.serializer.errors.items():
                self.add_error(field, exceptions.ValidationError(errors))

        return self.serializer.data

    def save(self, commit=True):
        self.instance = self.serializer.create(self.cleaned_data)

        return self.instance

    def save_m2m(self):
        # FIX-ME
        pass


class SerializerModeladmin:
    """Class decorator that initializes a `ModelAdmin` subclass with a given serializer type."""

    def __init__(self, serializer_class: Type[serializers.ModelSerializer]):
        self.serializer_class = serializer_class

    def __call__(self, modeladmin: Type[admin.ModelAdmin]) -> Type[admin.ModelAdmin]:
        modeladmin.form = SerializerForm.construct_modelform(self.serializer_class)
        modeladmin.readonly_fields = self.serializer_class.Meta.read_only_fields

        return modeladmin


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
            runner = task_runner.TaskRunner.get()
            await runner.schedule(coro_callable(modeladmin, request, queryset))

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

    async def schedule_task(self, coro_callable: Callable, **inputs):
        if self.store_result:
            scheduled_task = await models.ScheduledTask.schedule(coro_callable, **inputs)
            return scheduled_task.task_info['task']

        runner = task_runner.TaskRunner.get()
        task = await runner.schedule(coro_callable(**inputs))
        return task

    def __call__(self, coro_callable: Callable) -> Callable:
        @functools.wraps(coro_callable)
        async def action_coro_callable(modeladmin, request, queryset):
            tasks = []
            async for instance in queryset.all():
                task = await self.schedule_task(
                    coro_callable,
                    modeladmin=modeladmin, request=request, instance=instance)
                tasks.append(task)
            return tasks

        @admin.action(**self.kwargs)
        @functools.wraps(action_coro_callable)
        def action_callable(modeladmin, request, queryset):
            tasks = async_to_sync(action_coro_callable)(modeladmin, request, queryset)
            runner = task_runner.TaskRunner.get()

            for task_info in [runner.get_task_info(task) for task in tasks]:
                message_level = TASK_STATUS_MESSAGE_LEVEL[task_info['status']]
                modeladmin.message_user(
                    request,
                    f"Scheduled new task. Function: {action_coro_callable.__name__}. Status: {task_info['status']}.",
                    message_level)

        return action_callable

from asgiref.sync import async_to_sync

from typing import Type

from django import forms
from django.contrib import admin
from django.core import exceptions

from rest_framework import serializers

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


class MakeSerializerModeladmin:
    """Decorator that initializes a `ModelAdmin` subclass with a given serializer type."""

    def __init__(self, serializer_class: Type[serializers.ModelSerializer]):
        self.serializer_class = serializer_class

    def __call__(self, modeladmin: Type[admin.ModelAdmin]):
        modeladmin.form = SerializerForm.construct_modelform(self.serializer_class)
        modeladmin.readonly_fields = self.serializer_class.Meta.read_only_fields

        return modeladmin


def task_admin_action(method_name: str, **kwargs):
    async def action_callable(modeladmin, request, queryset):
        runner = task_runner.TaskRunner.get()

        async for instance in queryset.all():
            await runner.schedule(getattr(instance, method_name)())

    return admin.action(**kwargs)(async_to_sync(action_callable))

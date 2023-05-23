from typing import Type

from django import forms
from django.contrib import admin
from django.core import exceptions

from rest_framework import serializers


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


def make_serializer_modeladmin(serializer_class: Type[serializers.ModelSerializer]):
    """Type factory function that initializes a `ModelAdmin` subclass from the serializer type."""
    class SerializerModelAdmin(admin.ModelAdmin):
        form = SerializerForm.construct_modelform(serializer_class)
        readonly_fields = serializer_class.Meta.read_only_fields

    return SerializerModelAdmin

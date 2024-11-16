"""
This modules provides a basic Django admin site instance :py:const:`django_tasks.admin.site` that will display the
:py:class:`django_tasks.models.RegisteredTask`, :py:class:`django_tasks.models.DocTask` models, and that is capable of
implementing background task actions on any configured Django model (database table).
"""
import logging

from django.contrib import admin
from django.conf import settings
from django.db.models import QuerySet
from django.http import HttpRequest

from rest_framework.authtoken.models import Token
from rest_framework.authtoken.admin import TokenAdmin

from django_tasks import models
from django_tasks.admin_tools import AdminTaskAction, ChannelTasksAdminSite
from django_tasks.serializers import DocTaskSerializer
from django_tasks.typing import WSResponseJSON


#: The admin site instance to be configured and deployed.
site = ChannelTasksAdminSite()


@admin.register(models.RegisteredTask, site=site)
class RegisteredTaskModelAdmin(admin.ModelAdmin):
    def has_change_permission(self, request, obj=None):
        """
        A registered task must correctly correspond to a task function definition, so this must always
        return `False` to ban introducing inconsistencies.
        """
        return False

    def has_add_permission(self, request):
        """Task registration must be performed on task function definition, so this always returns `False`."""
        return False


site.register(Token, TokenAdmin)


if settings.DEBUG:
    @AdminTaskAction('django_tasks.tasks.doctask_access_test', description='Test async database access')
    def doctask_access_test(modeladmin: admin.ModelAdmin,
                            request: HttpRequest,
                            queryset: QuerySet,
                            ws_response: WSResponseJSON):
        objects_repr = str(queryset) if queryset.count() > 1 else str(queryset.first())
        logging.getLogger('django').info(
            'Requested to run DB access test on %s. Received response: %s.', objects_repr, ws_response)

    @AdminTaskAction('django_tasks.tasks.doctask_deletion_test', description='Test async database DELETE')
    def doctask_deletion_test(modeladmin: admin.ModelAdmin,
                              request: HttpRequest,
                              queryset: QuerySet,
                              ws_response: WSResponseJSON):
        objects_repr = str(queryset) if queryset.count() > 1 else str(queryset.first())
        logging.getLogger('django').info(
            'Requested to delete %s. Received response: %s.', objects_repr, ws_response)


@admin.register(models.DocTask, site=site)
class DocTaskModelAdmin(admin.ModelAdmin):
    list_display = ('registered_task', 'inputs', 'duration', *DocTaskSerializer.Meta.read_only_fields)

    if settings.DEBUG:
        actions = [doctask_access_test, doctask_deletion_test]

    def has_change_permission(self, request, obj=None):
        """Doc tasks must only be modified internally, so this always returns `False`."""
        return False

    def has_add_permission(self, request):
        """Doc tasks must only be created by task scheduling, so this always returns `False`."""
        return False

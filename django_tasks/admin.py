import asyncio
import logging

from django.contrib import admin
from django.conf import settings
from django.core.handlers.asgi import ASGIRequest
from django_tasks import models
from django_tasks.admin_tools import (
    SerializerModeladmin, AsyncAdminAction, AsyncAdminInstanceAction)
from django_tasks.serializers import ScheduledTaskSerializer


class AdminSite(admin.AdminSite):
    site_title = 'Stored Tasks'
    site_header = 'Stored Tasks'
    index_title = 'Tasks'


site = AdminSite()


@AsyncAdminAction(description='Test async deletion')
async def delete_test(modeladmin: admin.ModelAdmin,
                      request: ASGIRequest,
                      queryset):
    await queryset.adelete()


@AsyncAdminInstanceAction(description='Test async database access')
async def database_access_test(modeladmin: admin.ModelAdmin,
                               request: ASGIRequest,
                               instance: models.ScheduledTask):
    logging.getLogger('django').info('Retrieved %s', instance)
    await asyncio.sleep(10)


@AsyncAdminInstanceAction(description='Test async database access and store the task',
                          store_result=True)
async def store_database_access_test(modeladmin: admin.ModelAdmin,
                                     request: ASGIRequest,
                                     instance: models.ScheduledTask):
    await asyncio.sleep(10)
    return str(instance)


@admin.register(models.ScheduledTask, site=site)
@SerializerModeladmin(ScheduledTaskSerializer)
class ScheduledTaskModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'inputs', *ScheduledTaskSerializer.Meta.read_only_fields)
    if settings.DEBUG:
        actions = [database_access_test, store_database_access_test, delete_test]

    def has_change_permission(self, request, obj=None):
        return False

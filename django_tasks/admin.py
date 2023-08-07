import asyncio
import logging

from django.contrib import admin
from django.conf import settings
from django.core.handlers.asgi import ASGIRequest
from django.template import loader
from django.utils.safestring import mark_safe

from rest_framework.authtoken.models import Token
from rest_framework.authtoken.admin import TokenAdmin

from django_tasks import models
from django_tasks.admin_tools import AsyncAdminAction, AsyncAdminInstanceAction
from django_tasks.serializers import DocTaskSerializer


class AdminSite(admin.AdminSite):
    site_title = 'Stored Tasks'
    site_header = 'Stored Tasks'
    index_title = 'Index'


site = AdminSite()
site.register(Token, TokenAdmin)


@AsyncAdminAction(description='Test async deletion')
async def delete_test(modeladmin: admin.ModelAdmin,
                      request: ASGIRequest,
                      queryset):
    await queryset.adelete()


@AsyncAdminInstanceAction(description='Test async database access')
async def database_access_test(modeladmin: admin.ModelAdmin,
                               request: ASGIRequest,
                               instance: models.DocTask):
    logging.getLogger('django').info('Retrieved %s', repr(instance))
    await asyncio.sleep(10)


@AsyncAdminInstanceAction(description='Test async database access and store the task',
                          store_result=True)
async def store_database_access_test(modeladmin: admin.ModelAdmin,
                                     request: ASGIRequest,
                                     instance: models.DocTask):
    await asyncio.sleep(10)
    return str(instance)


@admin.register(models.DocTask, site=site)
class DocTaskModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'inputs', *DocTaskSerializer.Meta.read_only_fields)
    if settings.DEBUG:
        actions = [database_access_test, store_database_access_test, delete_test]

    @admin.display
    def status(self, doctask):
        return mark_safe(loader.render_to_string('task_status_display.html', dict(doctask=doctask)))

    def has_change_permission(self, request, obj=None):
        return False

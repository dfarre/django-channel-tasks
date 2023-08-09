from django.contrib import admin
from django.conf import settings

from rest_framework.authtoken.models import Token
from rest_framework.authtoken.admin import TokenAdmin

from django_tasks import models
from django_tasks.admin_task_actions import AdminTaskActionFactory
from django_tasks.serializers import DocTaskSerializer


class AdminSite(admin.AdminSite):
    site_title = 'Stored Tasks'
    site_header = 'Stored Tasks'
    index_title = 'Index'


site = AdminSite()
site.register(Token, TokenAdmin)


@admin.register(models.DocTask, site=site)
class DocTaskModelAdmin(admin.ModelAdmin):
    change_list_template = 'task_status_display.html'
    list_display = ('name', 'inputs', 'duration', *DocTaskSerializer.Meta.read_only_fields)
    if settings.DEBUG:
        actions = [
           AdminTaskActionFactory.new('doctask_access_test', description='Test async database access'),
           AdminTaskActionFactory.new('doctask_deletion_test', description='Test async deletion'),
        ]

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

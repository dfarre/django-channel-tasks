from django.core.handlers.asgi import ASGIRequest
from django.contrib import admin
from django.conf import settings

from rest_framework.authtoken.models import Token
from rest_framework.authtoken.admin import TokenAdmin

from django_tasks import models
from django_tasks.admin_task_actions import AdminTaskAction
from django_tasks.serializers import DocTaskSerializer


class AdminSite(admin.AdminSite):
    site_title = 'Stored Tasks'
    site_header = 'Stored Tasks'
    index_title = 'Index'


site = AdminSite()
site.register(Token, TokenAdmin)


@AdminTaskAction('doctask_access_test', description='Test async database access')
def doctask_access_test(modeladmin: admin.ModelAdmin, request: ASGIRequest, queryset):
    pass


@AdminTaskAction('doctask_deletion_test', description='Test async database DELETE')
def doctask_deletion_test(modeladmin: admin.ModelAdmin, request: ASGIRequest, queryset):
    pass


@admin.register(models.DocTask, site=site)
class DocTaskModelAdmin(admin.ModelAdmin):
    change_list_template = 'task_status_display.html'
    list_display = ('name', 'inputs', 'duration', *DocTaskSerializer.Meta.read_only_fields)

    if settings.DEBUG:
        actions = [doctask_access_test, doctask_deletion_test]

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

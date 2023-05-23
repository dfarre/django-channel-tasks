from django.contrib import admin

from django_tasks import models
from django_tasks.generic_forms import MakeSerializerModeladmin
from django_tasks.serializers import ScheduledTaskSerializer


class AdminSite(admin.AdminSite):
    site_title = 'Stored Tasks'
    site_header = 'Stored Tasks'
    index_title = 'Tasks'


site = AdminSite()


@admin.register(models.ScheduledTask, site=site)
@MakeSerializerModeladmin(ScheduledTaskSerializer)
class ScheduledTaskModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'inputs', *ScheduledTaskSerializer.Meta.read_only_fields)

    def has_change_permission(self, request, obj=None):
        return False

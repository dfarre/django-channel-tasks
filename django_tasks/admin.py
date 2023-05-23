from django.contrib import admin
from django.utils.safestring import mark_safe

from django_tasks import models, generic_forms, serializers
from django_tasks.generic_forms import make_serializer_modeladmin
from django_tasks.serializers import ScheduledTaskSerializer


class AdminSite(admin.AdminSite):
    site_title = 'Stored Tasks'
    site_header = 'Stored Tasks'
    index_title = 'Tasks'


site = AdminSite()


@admin.register(models.ScheduledTask, site=site)
class ScheduledTaskModelAdmin(make_serializer_modeladmin(ScheduledTaskSerializer)):
    list_display = ('name', 'inputs', *ScheduledTaskSerializer.Meta.read_only_fields)
    
    def has_change_permission(self, request, obj=None):
        return False
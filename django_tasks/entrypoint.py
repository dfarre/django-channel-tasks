import os
import sys


def manage_channel_tasks():
    os.environ['DJANGO_SETTINGS_MODULE'] = 'django_tasks.settings.base'

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)

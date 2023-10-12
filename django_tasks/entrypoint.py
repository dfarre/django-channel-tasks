import sys

from django.core.management import execute_from_command_line


def manage_channel_tasks():
    execute_from_command_line(sys.argv)

"""Ensures that django is set up with the base settings."""
import os

import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'django_tasks.settings.base'

django.setup()

#!/bin/bash
./setup-channel-tasks-docker/install-bootstrap.sh
./setup-channel-tasks-docker/init-django.sh
./setup-channel-tasks-docker/django-runserver.sh

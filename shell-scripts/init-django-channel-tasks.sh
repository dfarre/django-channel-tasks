#!/bin/bash
"${CHANNEL_TASKS_PYTHON_HOME}/bin/channel-tasks-admin" migrate --noinput
"${CHANNEL_TASKS_PYTHON_HOME}/bin/channel-tasks-admin" create_core_admin "${CHANNEL_TASKS_ADMIN_USER}" "${CHANNEL_TASKS_ADMIN_EMAIL}"
"${CHANNEL_TASKS_PYTHON_HOME}/bin/channel-tasks-admin" collectstatic --noinput

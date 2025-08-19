#!/bin/bash
"${CHANNEL_TASKS_PYTHON_HOME}/bin/channel-tasks-admin" migrate --noinput
"${CHANNEL_TASKS_PYTHON_HOME}/bin/channel-tasks-admin" create_task_admin "${TASK_ADMIN_USER}" "${TASK_ADMIN_EMAIL}"
"${CHANNEL_TASKS_PYTHON_HOME}/bin/channel-tasks-admin" collectstatic --noinput
"${CHANNEL_TASKS_PYTHON_HOME}/bin/channel-tasks-admin" sass-compiler --no-build

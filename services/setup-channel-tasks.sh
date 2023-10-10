#!/bin/bash
# Django setup
"${CHANNEL_TASKS_HOME}"/bin/channel-tasks-admin migrate --noinput
"${CHANNEL_TASKS_HOME}"/bin/channel-tasks-admin create_task_admin "${TASK_ADMIN_USER}" "${TASK_ADMIN_EMAIL}"
"${CHANNEL_TASKS_HOME}"/bin/channel-tasks-admin collectstatic --noinput

# Nginx-unit setup
export CHANNEL_TASKS_LISTENER_ADDRESS="*:${CHANNEL_TASKS_PORT}"
export CHANNEL_TASKS_PYTHON_HOME="${CHANNEL_TASKS_HOME}"
export CHANNEL_TASKS_PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
export CHANNEL_TASKS_ASGI_PATH="${CHANNEL_TASKS_HOME}/lib/python${CHANNEL_TASKS_PYTHON_VERSION}/site-packages"
envsubst '\$DJANGO_SECRET_KEY \$CHANNEL_TASKS_DB_PASSWORD \$CHANNEL_TASKS_INI_PATH \$CHANNEL_TASKS_PYTHON_HOME \$CHANNEL_TASKS_ASGI_PATH \$CHANNEL_TASKS_STATIC_ROOT \$CHANNEL_TASKS_STATIC_URI \$CHANNEL_TASKS_LISTENER_ADDRESS \$CHANNEL_TASKS_PYTHON_VERSION \$CHANNEL_TASKS_EMAIL_USER \$CHANNEL_TASKS_EMAIL_PASSWORD' \
 < "${CHANNEL_TASKS_HOME}"/channel-tasks-docker/channel-tasks-unit.template.json > "${CHANNEL_TASKS_HOME}"/channel-tasks-unit.json
curl -X PUT --data-binary @"${CHANNEL_TASKS_HOME}"/channel-tasks-unit.json --unix-socket /var/run/control.unit.sock http://localhost/config/
systemctl restart unit

#!/bin/bash
"${CHANNEL_TASKS_HOME}"/bin/channel-tasks-admin migrate --noinput
"${CHANNEL_TASKS_HOME}"/bin/channel-tasks-admin create_task_admin "${TASK_ADMIN_USER}" "${TASK_ADMIN_EMAIL}"
"${CHANNEL_TASKS_HOME}"/bin/channel-tasks-admin collectstatic --noinput
envsubst '\$CHANNEL_TASKS_INI_PATH \$CHANNEL_TASKS_PYTHON_HOME \$CHANNEL_TASKS_ASGI_PATH \$CHANNEL_TASKS_STATIC_ROOT \$CHANNEL_TASKS_STATIC_URI \$CHANNEL_TASKS_LISTENER_ADDRESS' \
 < "${CHANNEL_TASKS_HOME}"/channel-tasks-docker/channel-tasks-unit.template.json > "${CHANNEL_TASKS_HOME}"/channel-tasks-unit.json
curl -X PUT --data-binary @"${CHANNEL_TASKS_HOME}"/channel-tasks-unit.json --unix-socket /var/run/control.unit.sock http://localhost/config/
systemctl restart unit

#!/bin/bash
# Django setup
export DJANGO_SETTINGS_MODULE=django_tasks.settings.base

"${CHANNEL_TASKS_HOME}"/bin/channel-tasks-admin migrate --noinput
"${CHANNEL_TASKS_HOME}"/bin/channel-tasks-admin create_task_admin "${TASK_ADMIN_USER}" "${TASK_ADMIN_EMAIL}"
"${CHANNEL_TASKS_HOME}"/bin/channel-tasks-admin collectstatic --noinput

# Nginx-unit setup
export CHANNEL_TASKS_LISTENER_ADDRESS="*:${CHANNEL_TASKS_PORT}"
export CHANNEL_TASKS_PYTHON_HOME="${CHANNEL_TASKS_HOME}"
export CHANNEL_TASKS_PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
export CHANNEL_TASKS_ASGI_PATH="${CHANNEL_TASKS_HOME}/lib/python${CHANNEL_TASKS_PYTHON_VERSION}/site-packages"

envsubst '\$CHANNEL_TASKS_LISTENER_ADDRESS \$CHANNEL_TASKS_APP_NAME' \
    < "${CHANNEL_TASKS_HOME}"/channel-tasks-unit/listener.template.json > "${CHANNEL_TASKS_HOME}"/channel-tasks-unit/listener.json
envsubst '\$CHANNEL_TASKS_APP_NAME \$CHANNEL_TASKS_STATIC_ROOT \$CHANNEL_TASKS_STATIC_URI' \
    < "${CHANNEL_TASKS_HOME}"/channel-tasks-unit/routes.template.json > "${CHANNEL_TASKS_HOME}"/channel-tasks-unit/routes.json
envsubst '\$DJANGO_SETTINGS_MODULE \$DJANGO_SECRET_KEY \$CHANNEL_TASKS_USER \$CHANNEL_TASKS_DB_PASSWORD \$CHANNEL_TASKS_INI_PATH \$CHANNEL_TASKS_PYTHON_HOME \$CHANNEL_TASKS_ASGI_PATH \$CHANNEL_TASKS_PYTHON_VERSION \$CHANNEL_TASKS_EMAIL_USER \$CHANNEL_TASKS_EMAIL_PASSWORD' \
    < "${CHANNEL_TASKS_HOME}"/channel-tasks-unit/application.template.json > "${CHANNEL_TASKS_HOME}"/channel-tasks-unit/application.json

curl --unix-socket /var/run/control.unit.sock -X PUT --data-binary @"${CHANNEL_TASKS_HOME}"/channel-tasks-unit/application.json http://localhost/config/applications/"${CHANNEL_TASKS_APP_NAME}"
curl --unix-socket /var/run/control.unit.sock -X PUT --data-binary @"${CHANNEL_TASKS_HOME}"/channel-tasks-unit/routes.json http://localhost/config/routes/"${CHANNEL_TASKS_APP_NAME}"
curl --unix-socket /var/run/control.unit.sock -X PUT --data-binary @"${CHANNEL_TASKS_HOME}"/channel-tasks-unit/listener.json http://localhost/config/listeners/"${CHANNEL_TASKS_LISTENER_ADDRESS}"

systemctl restart unit

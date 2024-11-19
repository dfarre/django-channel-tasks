#!/bin/bash
BOOTSTRAP_VERSION=5.0.2
wget "https://github.com/twbs/bootstrap/archive/v${BOOTSTRAP_VERSION}.zip" -O bootstrap.zip
unzip bootstrap.zip
rm bootstrap.zip
mkdir -p django_tasks/static/bootstrap
mv bootstrap-$BOOTSTRAP_VERSION/** django_tasks/static/bootstrap/
rm -r bootstrap-$BOOTSTRAP_VERSION

"${CHANNEL_TASKS_PYTHON_HOME}/bin/channel-tasks-admin" migrate --noinput
"${CHANNEL_TASKS_PYTHON_HOME}/bin/channel-tasks-admin" create_task_admin "${TASK_ADMIN_USER}" "${TASK_ADMIN_EMAIL}"
"${CHANNEL_TASKS_PYTHON_HOME}/bin/channel-tasks-admin" collectstatic --noinput
"${CHANNEL_TASKS_PYTHON_HOME}/bin/channel-tasks-admin" sass-compiler --no-build

/usr/local/bin/docker-entrypoint.sh unitd
"${CHANNEL_TASKS_PYTHON_HOME}/bin/channel-tasks-admin" runserver "0.0.0.0:${CHANNEL_TASKS_WSGI_PORT}" > wsgi.log 2>&1 || cat wsgi.log

#!/bin/bash
BOOTSTRAP_VERSION=5.0.2
wget "https://github.com/twbs/bootstrap/archive/v${BOOTSTRAP_VERSION}.zip" -O bootstrap.zip
unzip bootstrap.zip
rm bootstrap.zip
mkdir -p django_tasks/static/bootstrap
mv bootstrap-$BOOTSTRAP_VERSION/** django_tasks/static/bootstrap/
rm -r bootstrap-$BOOTSTRAP_VERSION

sleep 2
channel-tasks-admin migrate --noinput
channel-tasks-admin create_task_admin "${TASK_ADMIN_USER}" "${TASK_ADMIN_EMAIL}"
channel-tasks-admin collectstatic --noinput
channel-tasks-admin sass-compiler --no-build
exec /usr/local/bin/docker-entrypoint.sh unitd --no-daemon &
sleep 2
channel-tasks-admin runserver "0.0.0.0:${CHANNEL_TASKS_WSGI_PORT}" > wsgi.log 2>&1 || cat wsgi.log

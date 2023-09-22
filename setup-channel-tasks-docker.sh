#!/bin/bash
sleep 3
channel-tasks-admin migrate --noinput
channel-tasks-admin create_task_admin "${TASK_ADMIN_USER}" "${TASK_ADMIN_EMAIL}"
channel-tasks-admin collectstatic --noinput

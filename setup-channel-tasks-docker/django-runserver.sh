#!/bin/bash
"${CHANNEL_TASKS_PYTHON_HOME}/bin/channel-tasks-admin" runserver "0.0.0.0:${CHANNEL_TASKS_WSGI_PORT}" > wsgi.log 2>&1 || cat wsgi.log

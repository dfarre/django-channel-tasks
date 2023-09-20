#!/bin/bash
docker compose -f "${CHANNEL_TASKS_DOCKER_HOME}/docker-compose.yml" up --build

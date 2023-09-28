FROM unit:1.31.0-python3.11

RUN apt-get -y update
RUN apt-get -y install git python3-pip python3-dev python3-venv postgresql-client locales gettext
RUN sed -i '/C.UTF-8/s/^# //g' /etc/locale.gen && locale-gen

WORKDIR /www
ADD . .

ARG CHANNEL_TASKS_PACKAGE
RUN python3 -m pip install --upgrade pip &&\
    python3 -m pip install $CHANNEL_TASKS_PACKAGE &&\
    python3 -m pip install tox

ARG DJANGO_SECRET_KEY
ARG CHANNEL_TASKS_DB_PASSWORD
ENV \
 CHANNEL_TASKS_PYTHON_HOME=/usr/local \
 CHANNEL_TASKS_STATIC_ROOT=/www/django_tasks \
 CHANNEL_TASKS_STATIC_URI=/static/ \
 CHANNEL_TASKS_ASGI_PATH=/www \
 CHANNEL_TASKS_LISTENER_ADDRESS=*:8001 \
 CHANNEL_TASKS_INI_PATH=/www/channel-tasks-docker.ini \
 CHANNEL_TASKS_PYTHON_VERSION=3.11 \
 CHANNEL_TASKS_DB_PASSWORD=$CHANNEL_TASKS_DB_PASSWORD \
 DJANGO_SECRET_KEY=$DJANGO_SECRET_KEY

RUN envsubst '\$DJANGO_SECRET_KEY \$CHANNEL_TASKS_PYTHON_VERSION \$CHANNEL_TASKS_INI_PATH \$CHANNEL_TASKS_DB_PASSWORD \$CHANNEL_TASKS_PYTHON_HOME \$CHANNEL_TASKS_ASGI_PATH \$CHANNEL_TASKS_STATIC_ROOT \$CHANNEL_TASKS_STATIC_URI \$CHANNEL_TASKS_LISTENER_ADDRESS' \
 < channel-tasks-unit.template.json > /docker-entrypoint.d/channel-tasks-unit.json

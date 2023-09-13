FROM unit:1.31.0-python3.11

RUN apt-get -y update
RUN apt-get -y install git python3-pip python3-dev python3-venv postgresql-client locales gettext
RUN sed -i '/C.UTF-8/s/^# //g' /etc/locale.gen && locale-gen

WORKDIR /www
ADD setup.py MANIFEST.in README.md version.ini .
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install -e .[dev,test]
RUN python3 -m pip install tox
ADD . .

ENV PYTHON_HOME=/usr/local ASGI_PATH=/www STATIC_SHARED_ROOT=/www/django_tasks STATIC_SHARED_URI=/static/ ASGI_PORT=8001

RUN envsubst '\$PYTHON_HOME \$ASGI_PATH \$STATIC_SHARED_ROOT \$STATIC_SHARED_URI \$ASGI_PORT' \
 < nginx-unit/channel-tasks-unit.json.template > /docker-entrypoint.d/channel-tasks-unit.json

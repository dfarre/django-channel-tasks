#!/bin/bash
wget "https://github.com/twbs/bootstrap/archive/v${BOOTSTRAP_VERSION}.zip" -O bootstrap.zip
unzip bootstrap.zip
rm bootstrap.zip
mkdir -p "${CHANNEL_TASKS_STATIC_ROOT}/bootstrap"
mv "bootstrap-${BOOTSTRAP_VERSION}/**" "${CHANNEL_TASKS_STATIC_ROOT}/bootstrap/"
rm -r "bootstrap-${BOOTSTRAP_VERSION}"

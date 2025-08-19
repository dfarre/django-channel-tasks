#!/bin/bash
wget "https://github.com/twbs/bootstrap/archive/v${BOOTSTRAP_VERSION}.zip" -O bootstrap.zip
unzip bootstrap.zip
rm bootstrap.zip
mkdir -p django_tasks/static/bootstrap
mv bootstrap-$BOOTSTRAP_VERSION/** django_tasks/static/bootstrap/
rm -r bootstrap-$BOOTSTRAP_VERSION

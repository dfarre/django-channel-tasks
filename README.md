# Django Channel Tasks
[![PyPI version](https://badge.fury.io/py/django-channel-tasks.svg)](https://badge.fury.io/py/django-channel-tasks) [![PyPI downloads](https://img.shields.io/pypi/dm/django-channel-tasks.svg)](https://img.shields.io/pypi/dm/django-channel-tasks)

A background task runner using `channels-redis` package.
It features:
* A REST API allowing to run defined tasks and store the results in PostgreSQL
* A simple implementation of asynchronous Django Admin tasks, scheduled through websocket

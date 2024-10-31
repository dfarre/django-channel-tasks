"""
This module provides the tools to import and validate task coroutine functions specified by their
dotted path. See its main function :py:func:`django_tasks.task_inspector.get_task_coro`.
"""
import collections
import inspect
import importlib

from typing import Any, Callable, Coroutine, Optional

from rest_framework import exceptions


class TaskCoroutine:
    def __init__(self, registered_task: str, **inputs: dict[str, Any]):
        self.registered_task = registered_task.strip()
        self.inputs = inputs
        self.module_path: str = ''
        self.name: str = ''
        self.callable: Callable = lambda: None

        if '.' in self.registered_task:
            self.module_path, self.name = self.registered_task.rsplit('.', 1)

        self.errors: dict[str, list[str]] = collections.defaultdict(list)
        self.check()

    @property
    def coroutine(self) -> Coroutine:
        """The coroutine instance ready to run in event loop."""
        return self.callable(**self.inputs)

    def check(self):
        self.check_coroutine()

        if self.callable:
            self.check_inputs()
        else:
            self.errors['name'].append(f"Coroutine '{self.registered_task}' not found.")

    def check_coroutine(self):
        try:
            module = importlib.import_module(self.module_path)
        except ImportError:
            module = None

        self.callable = getattr(module, self.name, None)

        if not inspect.iscoroutinefunction(self.callable):
            self.callable = None

    def check_inputs(self):
        params = inspect.signature(self.callable).parameters
        required_keys = set(k for k, v in params.items() if v.default == inspect._empty)
        optional_keys = set(k for k, v in params.items() if v.default != inspect._empty)

        input_keys = set(self.inputs)
        missing_keys = required_keys - input_keys
        unknown_keys = input_keys - required_keys - optional_keys

        if missing_keys:
            self.errors['inputs'].append(f'Missing required parameters {missing_keys}.')

        if unknown_keys:
            self.errors['inputs'].append(f'Unknown parameters {unknown_keys}.')


def get_task_coro(registered_task: str, inputs: dict[str, Any]) -> TaskCoroutine:
    """
    Tries to obtain a registered task coroutine taking the given inputs; raises a
    :py:class:`rest_framework.exceptions.ValidationError` on failure.

    :param registered_task: The full import dotted path of the coroutine function.
    :param inputs: Input parameters for the coroutine function.
    """
    task_coro = TaskCoroutine(registered_task, **inputs)

    if task_coro.errors:
        raise exceptions.ValidationError(task_coro.errors)

    return task_coro

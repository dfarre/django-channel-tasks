"""
This module provides the tools to import and validate task coroutine functions specified by their
dotted path. See its main function :py:func:`django_tasks.task_inspector.get_task_coro`.
"""
from __future__ import annotations

import collections
import inspect
import importlib

from typing import Callable, Coroutine

from rest_framework import exceptions

from django_tasks.typing import JSON


class TaskCoroutine:
    def __init__(self, registered_task: str, **inputs: JSON):
        self.inputs = inputs
        self.errors: dict[str, list[str]] = collections.defaultdict(list)
        self.set_callable(registered_task)

    @property
    def coroutine(self) -> Coroutine:
        """The coroutine instance ready to run in event loop."""
        return self.callable(**self.inputs)

    def set_callable(self, registered_task: str) -> None:
        if '.' not in registered_task:
            self.errors['registered_task'].append(f"Missing module name in import path '{registered_task}'.")
        else:
            module_path, name = registered_task.strip().rsplit('.', 1)

            try:
                module = importlib.import_module(module_path)
            except ImportError:
                self.errors['registered_task'].append(f"Cannot import module '{module_path}'.")
            else:
                callable = getattr(module, name, None)
                if inspect.iscoroutinefunction(callable):
                    self.check_inputs(callable)
                    self.callable: Callable[..., Coroutine] = callable
                else:
                    self.errors['registered_task'].append(f"Referenced object {callable} is not a coroutine function.")

    def check_inputs(self, callable: Callable):
        params = inspect.signature(callable).parameters
        required_keys = set(k for k, v in params.items() if v.default == inspect._empty)
        optional_keys = set(k for k, v in params.items() if v.default != inspect._empty)

        input_keys = set(self.inputs)
        missing_keys = required_keys - input_keys
        unknown_keys = input_keys - required_keys - optional_keys

        if missing_keys:
            self.errors['inputs'].append(f'Missing required parameters {missing_keys}.')

        if unknown_keys:
            self.errors['inputs'].append(f'Unknown parameters {unknown_keys}.')


def get_task_coro(registered_task: str, inputs: dict[str, JSON]) -> TaskCoroutine:
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

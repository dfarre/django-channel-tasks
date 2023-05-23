import collections
import inspect
import importlib

from typing import Callable, Optional, Any

from django.conf import settings


class TaskCoroInfo:
    def __init__(self, name: str, **inputs: dict[str, Any]):
        self.name = name.strip()
        self.inputs = inputs

    @property
    def callable(self) -> Optional[Callable]:
        module_names = settings.DJANGO_TASKS.get('coroutine_modules', [])

        for module_name in module_names:
            try:
                module = importlib.import_module(module_name)
            except ImportError:
                continue
            else:
                callable = getattr(module, self.name, None)

                if inspect.iscoroutinefunction(callable):
                    return callable
        else:
            return None

    @property
    def parameter_keys(self) -> Optional[tuple[set[str], set[str]]]:
        callable = self.callable

        if callable is None:
            return

        params = inspect.signature(callable).parameters
        required_keys = set(k for k, v in params.items() if v.default == inspect._empty)
        optional_keys = set(k for k, v in params.items() if v.default != inspect._empty)

        return required_keys, optional_keys

    @property
    def task_call_errors(self):
        errors = collections.defaultdict(list)

        if self.callable is None:
            errors['name'].append(f"Coroutine '{self.name}' not found.")
            return errors

        required_keys, optional_keys = self.parameter_keys
        input_keys = set(self.inputs)
        missing_keys = required_keys - input_keys
        unknown_keys = input_keys - required_keys - optional_keys

        if missing_keys:
            errors['inputs'].append(f'Missing required parameters {missing_keys}.')

        if unknown_keys:
            errors['inputs'].append(f'Unknown parameters {unknown_keys}.')

        return errors

import collections
import inspect
import importlib

from typing import Callable, Any


class TaskCoroInfo:
    _safe_coroutine_modules: set[str] = set()

    @classmethod
    def mark_as_safe(cls, callable: Callable):
        assert inspect.iscoroutinefunction(callable)
        cls._safe_coroutine_modules.add(inspect.getmodule(callable).__spec__.name)
        return callable

    def __init__(self, dotted_path: str, **inputs: dict[str, Any]):
        self.dotted_path = dotted_path.strip()
        self.inputs = inputs
        self.module_path, self.name, self.callable = '', '', None
        self.errors: dict[str, list[str]] = collections.defaultdict(list)
        self.check()

    def check(self):
        if '.' in self.dotted_path:
            self.module_path, self.name = self.dotted_path.rsplit('.', 1)

        if self.module_path in self._safe_coroutine_modules:
            self.check_coroutine()

        if self.callable:
            self.check_inputs()
        else:
            self.errors['name'].append(f"Coroutine '{self.dotted_path}' not found.")

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

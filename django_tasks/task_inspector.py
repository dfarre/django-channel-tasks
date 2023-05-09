import inspect
import importlib

from typing import Callable, Optional

from django.conf import settings


class TaskCoroInfo:
    def __init__(self, name: str):
        self.coroutine = self.get_coroutine(name)

    @staticmethod
    def get_coroutine(name: str) -> Optional[Callable]:
        method_name = name.strip()
        module_names = settings.DJANGO_TASKS.get('coroutine_modules', [])

        for module_name in module_names:
            try:
                module = importlib.import_module(module_name)
            except ImportError:
                pass
            else:
                callable = getattr(module, method_name, None)

                if inspect.iscoroutinefunction(callable):
                    return callable

    @property
    def parameters(self):
        coroutine = self.coroutine

        if coroutine is None:
            return

        params = inspect.signature(coroutine).parameters

        return params

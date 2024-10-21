from collections import defaultdict

import logging

from django.core.cache import cache


class TaskCache:
    """Handles the task cache of a user, using the configured Django cache."""

    def __init__(self, user_name: str):
        self.user_name = user_name

    @property
    def cache_key(self) -> str:
        return f'{self.user_name}.task_events'

    def get_index(self) -> str:
        return cache.get_or_set(self.cache_key, defaultdict(list))

    def clear_task_cache(self, task_id: str):
        """Clears a specific task cache, or logs a warning if not found."""
        current_index = self.get_index()

        if task_id in current_index:
            del current_index[task_id]
            cache.set(self.cache_key, current_index)
        else:
            logging.getLogger('django').warning('No cache found for %s.', task_id)

    def cache_task_event(self, task_id: str, event_content: dict):
        current_index = self.get_index()
        current_index[task_id].append(event_content)
        cache.set(self.cache_key, current_index)

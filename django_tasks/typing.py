"""Module that defines the custom `typing` types of this project, and some type assertion functions."""
from typing import Any, TypeAlias, TypedDict


#: Union type of all the flat JSON-serializable objects, lacking substructure.
FlatJSON: TypeAlias = str | float | int | bool | None

#: Generic, recursive JSON-serializable type.
JSON: TypeAlias = dict[str, 'JSON'] | list['JSON'] | FlatJSON

#: Generic JSON-serializable type for consumer events.
EventJSON = TypedDict('EventJSON', {'type': str, 'content': JSON})


#: JSON-serializable type for the task status data broadcasted by the task runner.
TaskStatusJSON = TypedDict('TaskStatusJSON', {
    'registered_task': str,
    'status': str,
    'http_status': int,
    'exception-repr': str,
    'output': JSON,
}, total=False)

#: JSON-serializable type for the content of task events broadcasted by the task runner.
TaskMessageJSON = TypedDict('TaskMessageJSON', {'task_id': str, 'detail': TaskStatusJSON})

#: Type for the web-socket responses.
WSResponseJSON = TypedDict('WSResponseJSON', {
    'request_id': str,
    'http_status': int,
    'details': list[JSON],
}, total=False)

#: JSON-serializable type for cache-clear request content.
CacheClearJSON = TypedDict('CacheClearJSON', {'task_id': str})

#: JSON-serializable type for a single-task schedule request content.
TaskJSON = TypedDict('TaskJSON', {'registered_task': str, 'inputs': dict[str, JSON]})

#: JSON-serializable type for a DocTask schedule request content.
DocTaskJSON = TypedDict('DocTaskJSON', {'id': int, 'registered_task': str, 'inputs': dict[str, JSON]})


def is_string_key_dict(value: Any) -> bool:
    return isinstance(value, dict) and all(isinstance(k, str) for k in value)


def is_string_key_dict_list(value: Any) -> bool:
    return isinstance(value, list) and all(is_string_key_dict(v) for v in value)


def is_string_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(v, str) for v in value)

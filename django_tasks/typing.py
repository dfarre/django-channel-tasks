import asyncio

from typing import TypeAlias, TypedDict


#: Union type of all the flat JSON-serializable objects, lacking substructure.
FlatJSON: TypeAlias = str | float | int | bool | None

#: Generic, recursive JSON-serializable type.
JSON: TypeAlias = dict[str, 'JSON'] | list['JSON'] | FlatJSON

#: Generic JSON-serializable type for consumer events.
EventJSON = TypedDict('EventJSON', {'type': str, 'content': JSON})


#: JSON-serializable type for the task status data broadcasted by the task runner.
TaskStatusJSON = TypedDict('TaskStatusJSON', {
    'status': str,
    'http_status': int,
    'exception-repr': str,
    'output': JSON,
}, total=False)

#: JSON-serializable type for the content of task events broadcasted by the task runner.
TaskMessageJSON = TypedDict('TaskMessageJSON', {
    'task_id': str,
    'registered_task': str,
    'details': list[TaskStatusJSON],
}, total=False)

#: Type of the web-socket messages that respond to requests.
WSResponseJSON = TypedDict('WSResponseJSON', {
    'request_id': str,
    'http_status': int,
    'details': list[JSON],
})

#: JSON-serializable type for cache-clear request content.
CacheClearJSON = TypedDict('CacheClearJSON', {'task_id': str})

#: JSON-serializable type for a single-task schedule request content.
TaskJSON = TypedDict('TaskJSON', {'registered_task': str, 'inputs': dict[str, JSON]})


#: Type for DocTask index entries, which relate the database ID with the task future.
DocTaskIndexEntry = TypedDict('DocTaskIndexEntry', {'id': int, 'future': asyncio.Future})

#: Type for the DocTask index, which relates the database ID with the task future by task ID.
DocTaskIndex: TypeAlias = dict[str, DocTaskIndexEntry]

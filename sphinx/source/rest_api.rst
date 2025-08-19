REST API
^^^^^^^^
This API is optional, to be employed whenever HTTP schedule requests are an interesting feature.

ASGI server endpoints
=====================

.. http:get:: /adrf/doctasks

   Lists doc-task documents, with the configured pagination.

   :query offset: Pagination offset number.
   :query limit: Pagination limit number.

   :reqheader Authorization: Token required to authenticate.

   **Examples**:

   .. include:: requests/asgi-get-adrfdoctasks.rst


.. http:post:: /api/doctasks/schedule

   Schedules doc-tasks.

   :reqheader Authorization: Token required to authenticate.

   **Examples**:

   .. include:: requests/asgi-post-apidoctasksschedule.rst


.. http:post:: /api/tasks/schedule

   Schedules tasks.

   :reqheader Authorization: Token required to authenticate.

   **Examples**:

   .. include:: requests/asgi-post-apitasksschedule.rst


WSGI server endpoints
=====================

.. http:post:: /api/doctasks/schedule

   Schedules doc-tasks through the ASGI endpoint.


.. http:post:: /api/doctasks

   Schedules a single doc-task through the ASGI endpoint.

   :reqheader Authorization: Token required to authenticate.

   **Examples**:

   .. include:: requests/wsgi-post-apidoctasks.rst

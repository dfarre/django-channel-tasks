REST API
^^^^^^^^
This API is optional, to be employed whenever HTTP schedule requests are an interesting feature.

ASGI server endpoints
=====================

.. http:post:: /api/doctasks/schedule

   Schedules doc-tasks.

   :reqheader Authorization: Token required to authenticate.

   `Response example 2 <post-from-api/doctasks/schedule-asgi-2_>`_ shows possible validation errors.

   .. include:: requests/asgi-post-apidoctasksschedule.rst


WSGI server endpoints
=====================

.. http:get:: /api/doctasks

   Lists doc-task documents, with the configured pagination.

   :query offset: Pagination offset number.
   :query limit: Pagination limit number.

   :reqheader Authorization: Token required to authenticate.

   .. include:: requests/wsgi-get-apidoctasks.rst


.. http:post:: /api/doctasks

   Schedules a single doc-task through local websocket.

   :reqheader Authorization: Token required to authenticate.

   .. include:: requests/wsgi-post-apidoctasks.rst

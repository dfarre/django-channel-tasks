REST API
^^^^^^^^
This API is optional, to be employed whenever HTTP schedule requests are an interesting feature.

ASGI server endpoints
=====================

.. http:get:: /adrf/doctasks/

   Lists doc-task documents, with the configured pagination.

   .. include:: requests/asgi_get.rst

   :query offset: Pagination offset number.
   :query limit: Pagination limit number.

   :reqheader Authorization: Token required to authenticate.


WSGI server endpoints
=====================

.. http:post:: /api/doctasks/

   Schedules doc-tasks.

   .. include:: requests/wsgi_post.rst

   :reqheader Authorization: Token required to authenticate.

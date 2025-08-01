Dependency graph
^^^^^^^^^^^^^^^^
The Python module dependency graph of the `django_tasks` package, as generated by `pydeps` (with `max-bacon=2` and excluding test, and Django settings, packages), is the following:

.. image:: images/pydeps.png
   :width: 98 %
   :align: center
   :alt: Pydeps graph


Therefore, this is basically a general-purpose `Django <https://www.djangoproject.com/>`_ application that integrates `Channels <https://channels.readthedocs.io/en/latest/>`_ and
(`async <https://pypi.org/project/adrf/>`_) `DRF <https://www.django-rest-framework.org/>`_; the `Websocket <https://pypi.org/project/websocket-client/>`_ library is employed by a
client that allows WSGI applications (Django Admin, DRF) to communicate through web-socket with ASGI applications (consumers) capable of managing background tasks with the Python
built-in `asyncio <https://docs.python.org/3.11/library/asyncio.html>`_ library.

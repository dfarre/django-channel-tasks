.. _get-to-api/doctasks-wsgi-1:

**[⇡] Request example 1**:

.. sourcecode:: http

   GET /api/doctasks?limit=2&offset=1 HTTP/1.1
   Authorization: Token ****************************************
   Content-type: application/json

.. _get-from-api/doctasks-wsgi-1:

**[⇣] Response example 1**:

.. sourcecode:: http

   HTTP/1.1 200 OK
   Content-type: application/json
   Allow: GET, POST, HEAD, OPTIONS
   X-frame-options: DENY
   Content-length: 680
   X-content-type-options: nosniff
   Referrer-policy: same-origin
   Cross-origin-opener-policy: same-origin
   
   {
       "count": 11,
       "next": "http://testserver/api/doctasks?limit=2&offset=3",
       "previous": "http://testserver/api/doctasks?limit=2",
       "results": [
           {
               "registered_task": "django_tasks.tasks.sleep_test",
               "inputs": {
                   "duration": 0.1,
                   "raise_error": true
               },
               "id": 6,
               "scheduled_at": "2025-09-22T21:56:03.150332Z",
               "completed_at": "2025-09-22T21:56:03.261143Z",
               "document": [
                   {
                       "status": "Error",
                       "http_status": 200,
                       "exception-repr": "Exception('Test error')"
                   }
               ]
           },
           {
               "registered_task": "django_tasks.tasks.sleep_test",
               "inputs": {
                   "duration": 0.8
               },
               "id": 4,
               "scheduled_at": "2025-09-22T21:56:03.060672Z",
               "completed_at": "2025-09-22T21:56:03.900564Z",
               "document": [
                   {
                       "output": "Slept for 0.8 seconds",
                       "status": "Success",
                       "http_status": 200
                   }
               ]
           }
       ]
   }

----

.. _get-to-api/doctasks-wsgi-2:

**[⇡] Request example 2**:

.. sourcecode:: http

   GET /api/doctasks?limit=1 HTTP/1.1
   Authorization: Token ****************************************
   Content-type: application/json

.. _get-from-api/doctasks-wsgi-2:

**[⇣] Response example 2**:

.. sourcecode:: http

   HTTP/1.1 200 OK
   Content-type: application/json
   Allow: GET, POST, HEAD, OPTIONS
   X-frame-options: DENY
   Content-length: 385
   X-content-type-options: nosniff
   Referrer-policy: same-origin
   Cross-origin-opener-policy: same-origin
   
   {
       "count": 12,
       "next": "http://testserver/api/doctasks?limit=1&offset=1",
       "previous": null,
       "results": [
           {
               "registered_task": "django_tasks.tasks.sleep_test",
               "inputs": {
                   "duration": 0.15,
                   "raise_error": true
               },
               "id": 5,
               "scheduled_at": "2025-09-22T21:56:03.061217Z",
               "completed_at": "2025-09-22T21:56:03.252107Z",
               "document": [
                   {
                       "status": "Error",
                       "http_status": 200,
                       "exception-repr": "Exception('Test error')"
                   }
               ]
           }
       ]
   }

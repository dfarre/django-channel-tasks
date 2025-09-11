----

*Request example 1*:

.. sourcecode:: http

   GET /api/doctasks?limit=2&offset=1 HTTP/1.1
   Authorization: Token *************************
   Content-type: application/json

*Response example 1*:

.. sourcecode:: http

   HTTP/1.1 200 OK
   Content-type: application/json
   Allow: GET, POST, HEAD, OPTIONS
   X-frame-options: DENY
   Content-length: 694
   X-content-type-options: nosniff
   Referrer-policy: same-origin
   Cross-origin-opener-policy: same-origin

   {
       "count": 10,
       "next": "http://testserver/api/doctasks?limit=2&offset=3",
       "previous": "http://testserver/api/doctasks?limit=2",
       "results": [
           {
               "registered_task": "django_tasks.tasks.sleep_test",
               "inputs": {
                   "duration": 4,
                   "raise_error": false
               },
               "id": 1,
               "scheduled_at": "2025-09-11T22:34:17.068666Z",
               "completed_at": "2025-09-11T22:34:21.089218Z",
               "document": [
                   {
                       "output": "Slept for 4 seconds",
                       "status": "Success",
                       "http_status": 200
                   }
               ]
           },
           {
               "registered_task": "django_tasks.tasks.sleep_test",
               "inputs": {
                   "duration": 8,
                   "raise_error": true
               },
               "id": 2,
               "scheduled_at": "2025-09-11T22:34:17.071717Z",
               "completed_at": "2025-09-11T22:34:25.097348Z",
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

----

*Request example 2*:

.. sourcecode:: http

   GET /api/doctasks?limit=1 HTTP/1.1
   Authorization: Token *************************
   Content-type: application/json

*Response example 2*:

.. sourcecode:: http

   HTTP/1.1 200 OK
   Content-type: application/json
   Allow: GET, POST, HEAD, OPTIONS
   X-frame-options: DENY
   Content-length: 382
   X-content-type-options: nosniff
   Referrer-policy: same-origin
   Cross-origin-opener-policy: same-origin

   {
       "count": 11,
       "next": "http://testserver/api/doctasks?limit=1&offset=1",
       "previous": null,
       "results": [
           {
               "registered_task": "django_tasks.tasks.sleep_test",
               "inputs": {
                   "duration": 1,
                   "raise_error": true
               },
               "id": 3,
               "scheduled_at": "2025-09-11T22:34:19.673896Z",
               "completed_at": "2025-09-11T22:34:20.690435Z",
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

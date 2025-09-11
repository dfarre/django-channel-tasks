----

*Request example 1*:

.. sourcecode:: http

   POST /api/doctasks HTTP/1.1
   Authorization: Token *************************
   Content-type: application/json

   {
       "registered_task": "django_tasks.tasks.sleep_test",
       "inputs": {
           "duration": 0.1,
           "raise_error": true
       }
   }

*Response example 1*:

.. sourcecode:: http

   HTTP/1.1 201 CREATED
   Content-type: application/json
   Allow: GET, POST, HEAD, OPTIONS
   X-frame-options: DENY
   Content-length: 113
   X-content-type-options: nosniff
   Referrer-policy: same-origin
   Cross-origin-opener-policy: same-origin

   {
       "request_id": "a64f248df8384827b6ba1736ddeefccb",
       "details": [
           {
               "status": "Started",
               "registered_task": "sleep_test"
           }
       ]
   }

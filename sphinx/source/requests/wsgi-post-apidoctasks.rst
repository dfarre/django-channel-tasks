.. _post-to-api/doctasks-wsgi-1:

**[⇡] Request example 1**:

.. sourcecode:: http

   POST /api/doctasks HTTP/1.1
   Authorization: Token a04a6414e6e06da44568c1d53cee59a83e855e0a
   Content-type: application/json
   
   {
       "registered_task": "django_tasks.tasks.sleep_test",
       "inputs": {
           "duration": 0.1,
           "raise_error": true
       }
   }

.. _post-from-api/doctasks-wsgi-1:

**[⇣] Response example 1**:

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
       "request_id": "ca292b3d91124feaa4e30f49432bc5b6",
       "details": [
           {
               "status": "Started",
               "registered_task": "sleep_test"
           }
       ]
   }

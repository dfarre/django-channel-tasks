*Request example*:

.. sourcecode:: http

   POST /api/doctasks HTTP/1.1
   Authorization: Token 71394aa521d07d0e3e339a3d1c3484ee6ef7986b
   Content-type: application/json
   
   {
       "registered_task": "django_tasks.tasks.sleep_test",
       "inputs": {
           "duration": 0.1,
           "raise_error": true
       }
   }

*Response example*:

.. sourcecode:: http

   HTTP/1.1 201 CREATED
   Content-type: application/json
   Allow: POST, HEAD, OPTIONS
   X-frame-options: DENY
   Content-length: 113
   X-content-type-options: nosniff
   Referrer-policy: same-origin
   Cross-origin-opener-policy: same-origin
   
   {
       "request_id": "871f7f2b380745668b4d94dc368d410e",
       "details": [
           {
               "status": "Started",
               "registered_task": "sleep_test"
           }
       ]
   }


.. _post-to-api/doctasks/schedule-asgi-1:

**[⇡] Request example 1**:

.. sourcecode:: http

   POST /api/doctasks/schedule HTTP/1.1
   Authorization: Token ***************
   Content-type: application/json

   [
       {
           "registered_task": "django_tasks.tasks.sleep_test",
           "inputs": {
               "duration": 0.995
           }
       },
       {
           "registered_task": "django_tasks.tasks.sleep_test",
           "inputs": {
               "duration": 0.95
           }
       },
       {
           "registered_task": "django_tasks.tasks.sleep_test",
           "inputs": {
               "duration": 0.94
           }
       },
       {
           "registered_task": "django_tasks.tasks.sleep_test",
           "inputs": {
               "duration": 0.8
           }
       },
       {
           "registered_task": "django_tasks.tasks.sleep_test",
           "inputs": {
               "duration": 0.15,
               "raise_error": true
           }
       }
   ]

.. _post-from-api/doctasks/schedule-asgi-1:

**[⇣] Response example 1**:

.. sourcecode:: http

   HTTP/1.1 201 CREATED
   Content-type: application/json
   Server: Unit/1.34.2
   Date: Fri, 19 Sep 2025 23:21:14 GMT
   Transfer-encoding: chunked

   {
       "request_id": "9cf2e204d9f846e4a647af73b999cc10"
   }

----

.. _post-to-api/doctasks/schedule-asgi-2:

**[⇡] Request example 2**:

.. sourcecode:: http

   POST /api/doctasks/schedule HTTP/1.1
   Authorization: Token ***************
   Content-type: application/json

   [
       {
           "registered_task": "django_tasks.foo.sleep_test",
           "inputs": {
               "duration": 4,
               "raise_error": false
           }
       },
       {
           "registered_task": "django_tasks.tasks.sleep_test",
           "inputs": {
               "wrong_key": true
           }
       }
   ]

.. _post-from-api/doctasks/schedule-asgi-2:

**[⇣] Response example 2**:

.. sourcecode:: http

   HTTP/1.1 400 BAD_REQUEST
   Content-type: application/json
   Server: Unit/1.34.2
   Date: Fri, 19 Sep 2025 23:21:14 GMT
   Transfer-encoding: chunked

   {
       "request_id": "d17e1520e99e40f6a82d1183d17c3f4a",
       "details": [
           {
               "registered_task": [
                   {
                       "message": "Object with dotted_path=django_tasks.foo.sleep_test does not exist.",
                       "code": "does_not_exist"
                   }
               ]
           },
           {
               "inputs": [
                   {
                       "message": "Missing required parameters {'duration'}.",
                       "code": "invalid"
                   },
                   {
                       "message": "Unknown parameters {'wrong_key'}.",
                       "code": "invalid"
                   }
               ]
           }
       ]
   }

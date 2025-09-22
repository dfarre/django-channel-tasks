.. _post-to-api/doctasks/schedule-asgi-1:

**[⇡] Request example 1**:

.. sourcecode:: http

   POST /api/doctasks/schedule HTTP/1.1
   Authorization: Token ****************************************
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
   Date: Mon, 22 Sep 2025 22:03:19 GMT
   Transfer-encoding: chunked
   
   {
       "request_id": "0dc86aaf2f5f4426a1bdb00a434ae054"
   }

----

.. _post-to-api/doctasks/schedule-asgi-2:

**[⇡] Request example 2**:

.. sourcecode:: http

   POST /api/doctasks/schedule HTTP/1.1
   Authorization: Token ****************************************
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
   Date: Mon, 22 Sep 2025 22:03:20 GMT
   Transfer-encoding: chunked
   
   {
       "request_id": "e362eafcb5294181ab76e47eb6c21064",
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

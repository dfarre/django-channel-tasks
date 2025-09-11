----

*Request example 1*:

.. sourcecode:: http

   POST /api/doctasks/schedule HTTP/1.1
   Authorization: Token *************************
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

*Response example 1*:

.. sourcecode:: http

   HTTP/1.1 201 CREATED
   Content-type: application/json
   Server: Unit/1.34.2
   Date: Thu, 11 Sep 2025 22:37:35 GMT
   Transfer-encoding: chunked

   {
       "request_id": "4976bbf34ea34d38a5d9ff747105186d"
   }

----

*Request example 2*:

.. sourcecode:: http

   POST /api/doctasks/schedule HTTP/1.1
   Authorization: Token *************************
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

*Response example 2*:

.. sourcecode:: http

   HTTP/1.1 400 BAD_REQUEST
   Content-type: application/json
   Server: Unit/1.34.2
   Date: Thu, 11 Sep 2025 22:37:35 GMT
   Transfer-encoding: chunked

   {
       "request_id": "b5228213acb64955a6c75ee52d87ec74",
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

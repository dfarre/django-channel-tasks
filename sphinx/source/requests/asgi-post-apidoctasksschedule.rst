*Request example*:

.. sourcecode:: http

   POST /api/doctasks/schedule HTTP/1.1
   Authorization: Token 71394aa521d07d0e3e339a3d1c3484ee6ef7986b
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

*Response example*:

.. sourcecode:: http

   HTTP/1.1 201 CREATED
   Content-type: application/json
   Server: Unit/1.32.1
   Date: Mon, 13 Jan 2025 20:40:39 GMT
   Transfer-encoding: chunked
   
   {
       "request_id": "ea63b1d5175440328c670e7da278ce88"
   }

*Request example*:

.. sourcecode:: http

   POST /api/doctasks/schedule HTTP/1.1
   Authorization: Token 71394aa521d07d0e3e339a3d1c3484ee6ef7986b
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

*Response example*:

.. sourcecode:: http

   HTTP/1.1 400 BAD_REQUEST
   Content-type: application/json
   Server: Unit/1.32.1
   Date: Mon, 13 Jan 2025 20:40:39 GMT
   Transfer-encoding: chunked
   
   {
       "request_id": "c323e4985ce4449488051f796882d675",
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


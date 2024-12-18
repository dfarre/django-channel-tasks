**Request example**:

.. sourcecode:: http

   POST /api/doctasks/schedule/ HTTP/1.1
   Authorization: Token ****************************
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

**Response example**:

.. sourcecode:: http

   HTTP/1.1 401 UNAUTHORIZED
   Content-type: application/json
   Www-authenticate: Token
   Allow: POST, OPTIONS
   X-frame-options: DENY
   Content-length: 27
   X-content-type-options: nosniff
   Referrer-policy: same-origin
   Cross-origin-opener-policy: same-origin

   {
       "detail": "Invalid token."
   }

**Request example**:

.. sourcecode:: http

   POST /api/doctasks HTTP/1.1
   Authorization: Token ****************************
   Content-type: application/json

   {
       "registered_task": "django_tasks.tasks.sleep_test",
       "inputs": {
           "duration": 0.1,
           "raise_error": true
       }
   }

**Response example**:

.. sourcecode:: http

   HTTP/1.1 401 UNAUTHORIZED
   Content-type: application/json
   Www-authenticate: Token
   Allow: POST, HEAD, OPTIONS
   X-frame-options: DENY
   Content-length: 27
   X-content-type-options: nosniff
   Referrer-policy: same-origin
   Cross-origin-opener-policy: same-origin

   {
       "detail": "Invalid token."
   }

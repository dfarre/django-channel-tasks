*Request example*:

.. sourcecode:: http

   GET /adrf/doctasks?limit=2&offset=1 HTTP/1.1
   Authorization: Token 85c6e0459b0568b51ae3939ff0380e12e89fd9e7
   Content-type: application/json

*Response example*:

.. sourcecode:: http

   HTTP/1.1 503 SERVICE_UNAVAILABLE
   Content-type: text/html
   Server: Unit/1.32.1
   Date: Mon, 06 Jan 2025 16:26:02 GMT
   Content-length: 54
   
   b'<!DOCTYPE html><title>Error 503</title><p>Error 503.\r\n'


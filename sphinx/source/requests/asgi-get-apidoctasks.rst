*Request example*:

.. sourcecode:: http

   GET /api/doctasks?limit=2&offset=1 HTTP/1.1
   Authorization: Token 71394aa521d07d0e3e339a3d1c3484ee6ef7986b
   Content-type: application/json

*Response example*:

.. sourcecode:: http

   HTTP/1.1 200 OK
   Content-type: application/json
   Server: Unit/1.32.1
   Date: Mon, 13 Jan 2025 20:40:39 GMT
   Transfer-encoding: chunked
   
   b'{}'

*Request example*:

.. sourcecode:: http

   GET /api/doctasks?limit=1 HTTP/1.1
   Authorization: Token 71394aa521d07d0e3e339a3d1c3484ee6ef7986b
   Content-type: application/json

*Response example*:

.. sourcecode:: http

   HTTP/1.1 200 OK
   Content-type: application/json
   Server: Unit/1.32.1
   Date: Mon, 13 Jan 2025 20:40:39 GMT
   Transfer-encoding: chunked
   
   b'{}'


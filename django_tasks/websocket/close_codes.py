"""Gathers and names websocket close codes (Websocket ref: https://datatracker.ietf.org/doc/html/rfc6455)."""
import websocket

OK = websocket.STATUS_NORMAL
GOING_AWAY = websocket.STATUS_GOING_AWAY
BAD_GATEWAY = websocket.STATUS_BAD_GATEWAY

UNAUTHORIZED = 3000
FORBIDDEN = 3003
TIMEOUT = 3008

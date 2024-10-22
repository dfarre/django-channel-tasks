"""Named websocket close codes."""
import websocket

OK = websocket.STATUS_NORMAL
GOING_AWAY = websocket.STATUS_GOING_AWAY
BAD_GATEWAY = websocket.STATUS_BAD_GATEWAY

UNAUTHORIZED = 3000
FORBIDDEN = 3003
TIMEOUT = 3008

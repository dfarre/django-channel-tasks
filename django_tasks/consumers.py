from channels.generic.websocket import AsyncJsonWebsocketConsumer


class TaskStatusConsumer(AsyncJsonWebsocketConsumer):
    groups = ['tasks']

    async def task_done(self, event):
        """Echoes the task-done document."""
        await self.send_json(content=event["content"])

    async def connect(self):
        # To accept the connection call:
        await self.accept()

        # Or accept the connection and specify a chosen subprotocol.
        # A list of subprotocols specified by the connecting client
        # will be available in self.scope['subprotocols']
        # await self.accept("subprotocol")

        # To reject the connection, call:
        # await self.close()

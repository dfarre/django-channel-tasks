from channels.generic.websocket import AsyncJsonWebsocketConsumer


class TaskStatusConsumer(AsyncJsonWebsocketConsumer):
    groups = ['tasks']

    async def task_done(self, event):
        """Echoes the task-done document."""
        await self.send_json(content=event["content"])

    async def task_started(self, event):
        """Echoes the task-started document."""
        await self.send_json(content=event["content"])

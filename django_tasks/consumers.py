from channels.generic.websocket import AsyncJsonWebsocketConsumer

from django_tasks import task_runner
from django_tasks.serializers import DocTaskSerializer


class TaskStatusConsumer(AsyncJsonWebsocketConsumer):
    groups = ['tasks']

    async def task_success(self, event):
        """Echoes the task.success document."""
        await self.send_json(content=event["content"])

    async def task_started(self, event):
        """Echoes the task.started document."""
        await self.send_json(content=event["content"])

    async def task_cancelled(self, event):
        """Echoes the task.cancelled document."""
        await self.send_json(content=event["content"])

    async def task_error(self, event):
        """Echoes the task.error document."""
        await self.send_json(content=event["content"])

    async def receive_json(self, content):
        """Pocesses task schedule requests."""
        serializer = DocTaskSerializer(data=content)
        serializer.is_valid(raise_exception=True)
        runner = task_runner.TaskRunner.get()
        await runner.schedule(serializer.callable(**serializer.data['inputs']))

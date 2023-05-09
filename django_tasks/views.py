from asgiref.sync import async_to_sync

from rest_framework import response, status, viewsets

from django_tasks import models, serializers
from django_tasks.task_runner import TaskRunner


class TaskViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'delete', 'head', 'options', 'trace']
    queryset = models.ScheduledTask.objects.all()
    serializer_class = serializers.ScheduledTaskSerializer
    task_runner: TaskRunner

    def get_queryset(self):
        return models.ScheduledTask.objects.all()

    def setup_task_runner(self):
        """Starts a (single) worker thread for the view."""
        self.task_runner = TaskRunner()
        self.task_runner.worker_thread.start()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.setup_task_runner()
        async_to_sync(serializer.schedule_task)(self.task_runner)

        return response.Response(status=status.HTTP_201_CREATED, data=serializer.data)

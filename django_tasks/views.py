from rest_framework import viewsets

from django_tasks import models, serializers
from django_tasks.task_runner import TaskRunner


class TaskViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'delete', 'head', 'options', 'trace']
    queryset = models.ScheduledTask.objects.all()
    serializer_class = serializers.ScheduledTaskSerializer
    task_runner: TaskRunner = TaskRunner()

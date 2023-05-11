from rest_framework import viewsets

from django_tasks import models, serializers


class TaskViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'delete', 'head', 'options', 'trace']
    queryset = models.ScheduledTask.objects.all()
    serializer_class = serializers.ScheduledTaskSerializer

from rest_framework import decorators, response, status, viewsets

from django_tasks import models, serializers


class TaskViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'delete', 'head', 'options', 'trace']
    queryset = models.DocTask.objects.all()
    serializer_class = serializers.DocTaskSerializer

    @decorators.action(detail=False, methods=['post'])
    def schedule(self, request, *args, **kwargs):
        """Schedules an array of tasks."""
        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response(data=serializer.data, status=status.HTTP_201_CREATED)

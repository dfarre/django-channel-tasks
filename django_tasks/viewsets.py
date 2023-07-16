from rest_framework import decorators, response, status, viewsets

from django_tasks import models, serializers


class TaskViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'delete', 'head', 'options', 'trace']
    queryset = models.DocTask.objects.all()
    serializer_class = serializers.DocTaskSerializer

    @decorators.action(detail=False, methods=['post'])
    def schedule(self, request, *args, **kwargs):
        """DRF action that schedules an array of tasks."""
        many_serializer, _ = self.serializer_class.create_doctask_group(
            request.data, context=self.get_serializer_context())

        return response.Response(data=many_serializer.data, status=status.HTTP_201_CREATED)

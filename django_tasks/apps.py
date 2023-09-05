from django import apps


class TasksConfig(apps.AppConfig):
    name = 'django_tasks'
    verbose_name = 'Documenting Tasks'

    def ready(self):
        from django_tasks import tasks  # noqa

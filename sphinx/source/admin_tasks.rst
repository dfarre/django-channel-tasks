Extending the Django Admin site
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Implementing background task actions on a configured Django model is as follows. In the `admin.py` module::

   from django_tasks.admin import site
   ...

   @AdminTaskAction('<registered task coro>', description='<Action description>')
   def new_model_task(modeladmin: ModelAdmin,
                      request: HttpRequest,
                      queryset: QuerySet,
                      ws_response: WSResponseJSON):
      # Will be executed after the task is scheduled, taking the web-socket response received.
      ...

   @django.contrib.admin.register(NewModel, site=site)
   class NewModelAdmin(ModelAdmin):
      actions = [new_model_task, ...]
      ...

The task coroutine must be previously registered as::

   @RegisteredTask.register
   async def registered_task_name(instance_ids: list[int]):
      def instance_function(instance):
         ...

      await ModelTask('<app name>', '<model name>', instance_function)(instance_ids)

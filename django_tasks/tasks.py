import asyncio
import logging

from django_tasks import models
from django_tasks.task_inspector import TaskCoroInfo


@TaskCoroInfo.mark_as_safe
async def sleep_test(duration, raise_error=False):
    logging.getLogger('django').info('Starting sleep test.')
    await asyncio.sleep(duration)

    if raise_error:
        logging.getLogger('django').info('Sleep test done with raise.')
        raise Exception('Test error')

    logging.getLogger('django').info('Sleep test done with no raise.')
    return f"Slept for {duration} seconds"


@TaskCoroInfo.mark_as_safe
async def doctask_access_test(instance_ids: list[int]):
    await asyncio.sleep(3)
    async for doctask in models.DocTask.objects.filter(pk__in=instance_ids):
        logging.getLogger('django').info('Retrieved %s', repr(doctask))
    await asyncio.sleep(3)


@TaskCoroInfo.mark_as_safe
async def doctask_deletion_test(instance_ids: list[int]):
    await asyncio.sleep(3)
    await models.DocTask.objects.filter(pk__in=instance_ids).adelete()
    logging.getLogger('django').info('Deleted doctasks %s', instance_ids)
    await asyncio.sleep(3)

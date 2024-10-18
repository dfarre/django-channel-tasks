import asyncio
import logging
import time

from django_tasks.admin_tools import ModelTask


async def sleep_test(duration, raise_error=False):
    logging.getLogger('django').info('Starting sleep test.')
    await asyncio.sleep(duration)

    if raise_error:
        logging.getLogger('django').info('Sleep test done with raise.')
        raise Exception('Test error')

    logging.getLogger('django').info('Sleep test done with no raise.')
    return f"Slept for {duration} seconds"


async def doctask_access_test(instance_ids: list[int]):
    def instance_function(doctask):
        time.sleep(1)
        logging.getLogger('django').info('Retrieved %s', repr(doctask))
        time.sleep(1)

    await ModelTask('django_tasks', 'DocTask', instance_function)(instance_ids)
    await asyncio.sleep(4)


async def doctask_deletion_test(instance_ids: list[int]):
    def instance_function(doctask):
        doctask.delete()
        logging.getLogger('django').info('Deleted %s', repr(doctask))
        time.sleep(1)

    await ModelTask('django_tasks', 'DocTask', instance_function)(instance_ids)

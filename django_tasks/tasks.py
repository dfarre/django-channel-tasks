import asyncio


async def sleep_test(duration=1, raise_error=False):
    await asyncio.sleep(duration)

    if raise_error:
        raise Exception('Test error')

    return f"Slept for {duration} seconds"

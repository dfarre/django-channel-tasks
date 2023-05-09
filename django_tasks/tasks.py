import asyncio


async def sleep_test(duration=1):
    await asyncio.sleep(duration)
    return f"Slept for {duration} seconds"

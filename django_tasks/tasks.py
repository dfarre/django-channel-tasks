import asyncio


async def sleep(duration=1):
    asyncio.sleep(duration)
    return f"Slept for {duration} seconds"

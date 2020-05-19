import asyncio
import pytest
from toad_sp_data.loop import Loop

_LOOP_NUMBER = 3  # loops to be created at tests


@pytest.mark.asyncio
async def test_loop():
    async def asleep(x):
        await asyncio.sleep(x)

    event_loop = asyncio.get_event_loop()

    loops = [Loop(asleep, (3,)) for _ in range(_LOOP_NUMBER + 1)]
    for loop in loops:
        loop.start(event_loop)
    for loop in loops:
        await loop.stop()

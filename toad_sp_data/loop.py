import asyncio
from typing import Any, Callable, Tuple


class Loop:
    def __init__(self, async_func: Callable[..., Any], arguments: Tuple[Any, ...]):
        """
        A wrapper to run an asynchronous function in a loop until manually
        cancelled.

        :param async_func: asynchronous function to run
        :param arguments: arguments to pass to said function
        """

        async def func(*args: Any):
            """
            Wrapper function for async_func to ensure it stops at
            asyncio.CancelledError unless implemented otherwise inside
            async_func.

            :param args: args to pass to async_function
            :return: None
            """
            try:
                while True:
                    await async_func(*args)
            except asyncio.CancelledError:
                pass

        self.func = func
        self.args = arguments
        self.task: asyncio.Task = None

    def start(self, event_loop: asyncio.AbstractEventLoop) -> None:
        """
        Create an asyncio.Task for self.func which will run async_func.

        :return: None
        """
        self.task = event_loop.create_task(self.func(*self.args))

    async def stop(self) -> None:
        """
        Cancel self.func and wait for the cancellation to finish.

        :return: None
        """
        self.task.cancel()
        try:
            await self.task
        except asyncio.CancelledError:
            pass

import asyncio
from collections.abc import Callable


class EventHandler:
    """this class enables calling handlers upon events.
    this is so services in different layers can be called
    """

    def __init__(self, *args, **kwargs):
        self._event_handlers: dict[str, list[Callable]] = {}
        super().__init__(*args, **kwargs)

    def on(self, event: str, handler: Callable):
        """Register a handler for a named event.
        handler signature: async/sync (guild_id: int, **kwargs)
        """
        self._event_handlers.setdefault(event, []).append(handler)

    async def _emit(self, event: str, guild_id: int, **kwargs):
        for handler in self._event_handlers.get(event, []):
            import inspect

            params = inspect.signature(handler).parameters
            if "event" in params:
                kwargs["event"] = event
            if asyncio.iscoroutinefunction(handler):
                await handler(guild_id, **kwargs)
            else:
                handler(guild_id, **kwargs)

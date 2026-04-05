from abc import ABC, abstractmethod
from .ws_hooks_router import HookMeta
from .ws_manager import ws_manager
from .models import WSResponse


class WebsocketHook(ABC, metaclass=HookMeta):
    """Attach this as a parent to register as a websocket hook."""

    events: list[str] = []

    def __init__(self, guild_id: int):
        self.guild_id = guild_id

    @abstractmethod
    async def handle(self):
        pass

    async def send(self, response: WSResponse):
        """mimics `ws_manager.send()`"""
        await ws_manager.send(self.guild_id, response.model_dump())

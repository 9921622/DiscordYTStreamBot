from abc import ABC, abstractmethod
from enum import IntFlag, auto

from .ws_commands_router import CommandMeta
from .models import WSResponse


class WSCommandFlags(IntFlag):
    NONE = 0
    BROADCAST = auto()
    BROADCAST_STATUS = auto()


class WebsocketCommand(ABC, metaclass=CommandMeta):
    """Attach this as a parent to register as a websocket command.
    See CommandMeta to see how its attached to list
    """

    prefix: str = None
    flags: WSCommandFlags = WSCommandFlags.NONE

    def __init__(self, websocket, guild_id: int, data: dict):
        self.websocket = websocket
        self.guild_id = guild_id
        self.data = data
        self.get_objects()
        self.errors = self.get_errors()

    def get_objects(self):
        pass

    def get_errors(self):
        return None

    @abstractmethod
    async def handle(self):
        """main logic"""

    def response(self, **data):
        return WSResponse(type=self.prefix, success=True, data=data or None).model_dump()

    def response_error(self, msg, **detail):
        return WSResponse(
            type=self.prefix,
            success=False,
            error={
                "message": msg,
                "detail": detail or None,
            },
        ).model_dump()

    async def execute(self):
        """will be called by ws_commands_router"""
        errors = self.get_errors()
        if errors is not None:
            return self.response_error(msg="Validation failed", **errors), None, None

        result = await self.handle()

        if isinstance(result, dict) and result.get("error") is not None:
            return result, None, None

        from bot.bot import bot

        guild_broadcast = result if self.flags & WSCommandFlags.BROADCAST else None

        status_broadcast = (
            WSResponse(
                type="status", success=True, data={"playback": bot.vc_get_status(self.guild_id).model_dump()}
            ).model_dump()
            if self.flags & WSCommandFlags.BROADCAST_STATUS
            else None
        )
        return result, guild_broadcast, status_broadcast

from abc import ABCMeta, ABC, abstractmethod

_ws_commands: dict[str, type["WebsocketCommand"]] = {}


class CommandMeta(ABCMeta):
    """metaclass for adding class to _ws_commands"""

    def __new__(cls, name, bases, attrs):
        new_cls = super().__new__(cls, name, bases, attrs)

        # using the prefix add to _ws_commands
        prefix = attrs.get("prefix")
        if prefix:
            if prefix in _ws_commands:
                raise Exception(f"Duplicate WS command '{prefix}'")

            _ws_commands[prefix] = new_cls

        return new_cls


class WebsocketCommand(ABC, metaclass=CommandMeta):
    """Attach this as a parent to register as a websocket command"""

    prefix: str = None
    broadcast: bool = False
    broadcast_status: bool = False

    def __init__(self, websocket, guild_id: int, data: dict):
        self.websocket = websocket
        self.guild_id = guild_id
        self.data = data

    @abstractmethod
    async def handle(self):
        """Main logic"""
        pass

    def response(self, **kwargs):
        return {"type": self.prefix, **kwargs}

    def response_error(self, msg, **kwargs):
        return {"error": msg, **kwargs}

    async def execute(self):
        result = await self.handle()

        if isinstance(result, dict) and "error" in result:
            return result, None, None

        from bot.bot import bot

        guild_broadcast = result if self.broadcast else None
        status_broadcast = (
            {
                "type": "status",
                "playback": bot.vc_get_status(self.guild_id).model_dump(),
            }
            if self.broadcast_status
            else None
        )

        return result, guild_broadcast, status_broadcast


async def ws_command_router(websocket, message: dict):
    """returns response based on command. used in the websockets route"""
    cmd = message.get("type")
    guild_id = message.get("guild_id")

    if not cmd:
        return {"error": "missing 'type'"}, None, None
    if not guild_id:
        return {"error": "missing 'guild_id'"}, None, None

    command_cls = _ws_commands.get(cmd)
    if not command_cls:
        return {"error": f"unknown command '{cmd}'"}, None, None

    try:
        command = command_cls(websocket, guild_id, message)
        return await command.execute()

    except Exception as e:
        import traceback

        traceback.print_exc()
        return {"error": str(e)}, None, None

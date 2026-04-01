import functools
from collections.abc import Callable

_ws_commands: dict[str, tuple[Callable, bool, bool]] = {}  # (handler, broadcast, broadcast_status)


class WSRouter:

    def __init__(self):
        self._routes: dict[str, tuple[Callable, bool, bool]] = {}

    def command(self, prefix: str = None, broadcast: bool = False, broadcast_status: bool = False):
        if not prefix:
            raise Exception("prefix required")

        def decorator(f: Callable):
            @functools.wraps(f)
            async def wrapper(websocket, guild_id: int, data: dict):
                print(f"[ws_command] {prefix} | guild={guild_id} | data={data}")
                return await f(websocket, guild_id, data)

            if prefix in self._routes:
                raise Exception(f"WSRouter: '{prefix}' is already registered")

            self._routes[prefix] = (wrapper, broadcast, broadcast_status)
            return wrapper

        return decorator

    def initialize(self):
        for prefix, entry in self._routes.items():
            if prefix in _ws_commands:
                raise Exception(f"WSRouter: '{prefix}' conflicts with an existing command")
            _ws_commands[prefix] = entry


async def ws_command_router(websocket, message: dict):
    from api.websockets.ws_manager import ws_manager
    from bot.bot import bot

    cmd = message.get("type")
    guild_id = message.get("guild_id")

    if not cmd:
        return {"error": "missing 'type' field"}, None, None
    if not guild_id:
        return {"error": "missing 'guild_id' field"}, None, None

    entry = _ws_commands.get(cmd)
    if not entry:
        return {"error": f"unknown command '{cmd}'"}, None, None

    handler, broadcast, broadcast_status = entry

    try:
        result = await handler(websocket, guild_id, message)

        if isinstance(result, dict) and "error" in result:
            return result, None, None

        guild_broadcast = result if broadcast else None
        status_broadcast = {"type": "status", "playback": bot.vc_get_status(guild_id)} if broadcast_status else None

        return result, guild_broadcast, status_broadcast

    except Exception as e:
        return {"error": str(e)}, None, None

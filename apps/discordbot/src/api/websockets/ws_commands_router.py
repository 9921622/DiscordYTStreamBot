from abc import ABCMeta

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

from abc import ABCMeta
from bot.bot_hooks import hooks

_ws_hooks: dict[str, list[type["WebsocketHook"]]] = {}


class HookMeta(ABCMeta):
    def __new__(cls, name, bases, attrs):
        new_cls = super().__new__(cls, name, bases, attrs)

        events = attrs.get("events", [])
        for event in events:
            if event not in _ws_hooks:
                _ws_hooks[event] = []
            _ws_hooks[event].append(new_cls)

        return new_cls


async def ws_hook_router(event: str, guild_id: int):
    """Call all hooks registered for an event. Used in bot_hooks."""
    hook_classes = _ws_hooks.get(event, [])

    for hook_cls in hook_classes:
        try:
            await hook_cls(guild_id).handle()
        except Exception:
            import traceback

            traceback.print_exc()


@hooks("on_disconnect", "on_voice_connect", "on_voice_disconnect", "on_song_start", "on_song_end")
async def _handler(guild_id: int, event: str):
    await ws_hook_router(event, guild_id)


def get_registered_hooks():
    return list(_ws_hooks.keys())

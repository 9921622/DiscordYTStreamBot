from settings import settings


class DiscordBotDebug:

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._debug_server_id: int | None = settings.DISCORD_DEBUG_SERVER
        self._debug_vc_id: int | None = settings.DISCORD_DEBUG_VC
        self._debug_channel_id: int | None = settings.DISCORD_DEBUG_CHANNEL

    @property
    def debug_server(self):
        return self.get_guild(self._debug_server_id) if self._debug_server_id else None

    @property
    def debug_vc(self):
        return self.get_channel(self._debug_vc_id) if self._debug_vc_id else None

    @property
    def debug_channel(self):
        return self.get_channel(self._debug_channel_id) if self._debug_channel_id else None

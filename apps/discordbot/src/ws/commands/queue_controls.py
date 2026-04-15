from bot.bot import bot
from utils.api_backend_wrapper import VideoAPI, GuildPlaylistAPI
from ws.ws_command import WebsocketCommand, WSCommandFlags
from .mixins import DiscordUserMixin


class QueueGetCommand(DiscordUserMixin, WebsocketCommand):
    prefix = "queue-get"

    async def handle(self):
        rw = await GuildPlaylistAPI.get(self.guild_id)
        if not rw.response.is_success:
            return self.response_error("failed to get queue", detail=rw.response.json())
        return self.response(playlist=rw.data.model_dump())


class QueueAddCommand(DiscordUserMixin, WebsocketCommand):
    prefix = "queue-add"
    flags = WSCommandFlags.BROADCAST

    def get_objects(self):
        super().get_objects()
        self.youtube_id = self.data.get("youtube_id")

    def get_errors(self):
        if not self.youtube_id:
            return self.response_error("missing 'youtube_id'")
        return super().get_errors()

    async def handle(self):
        rw = await GuildPlaylistAPI.add_song(self.guild_id, self.youtube_id, self.user_id)
        if not rw.response.is_success:
            return self.response_error("failed to add item", detail=rw.response.json())
        return self.response(playlist=rw.data.model_dump())


class QueueRemoveCommand(DiscordUserMixin, WebsocketCommand):
    prefix = "queue-remove"
    flags = WSCommandFlags.BROADCAST

    def get_objects(self):
        super().get_objects()
        self.item_id = self.data.get("item_id")

    def get_errors(self):
        if not self.item_id:
            return self.response_error("missing 'item_id'")
        return super().get_errors()

    async def handle(self):
        rw = await GuildPlaylistAPI.remove_song(self.guild_id, self.item_id)
        if not rw.response.is_success:
            return self.response_error("failed to remove item", detail=rw.response.json())
        return self.response(playlist=rw.data.model_dump())


class QueueReorderCommand(DiscordUserMixin, WebsocketCommand):
    prefix = "queue-reorder"
    flags = WSCommandFlags.BROADCAST

    def get_objects(self):
        super().get_objects()
        self.order = self.data.get("order")

    def get_errors(self):
        if not self.order or not isinstance(self.order, list):
            return self.response_error("missing or invalid 'order'")
        return super().get_errors()

    async def handle(self):
        rw = await GuildPlaylistAPI.reorder(self.guild_id, self.order)
        if not rw.response.is_success:
            return self.response_error("failed to reorder queue", detail=rw.response.json())
        return self.response(playlist=rw.data.model_dump())


class QueueClearCommand(DiscordUserMixin, WebsocketCommand):
    prefix = "queue-clear"
    flags = WSCommandFlags.BROADCAST

    async def handle(self):
        rw = await GuildPlaylistAPI.clear(self.guild_id)
        if not rw.response.is_success:
            return self.response_error("failed to clear queue", detail=rw.response.json())
        return self.response(playlist=rw.data.model_dump())


async def _play_current_item(command: WebsocketCommand, guild_playlist) -> bool:
    """Fetch source and start playback for playlist.current_item.
    Returns True on success, or calls command.response_error and returns False."""
    current_item = guild_playlist.current_item
    if current_item is None:
        return command.response_error("playlist has no current item")

    rw_source = await VideoAPI.get_source(current_item.video.youtube_id)
    if not rw_source.response.is_success:
        return command.response_error("failed to get video source", detail=rw_source.response.json())

    try:
        await bot.vc_play(
            command.guild_id,
            current_item.video.youtube_id,
            rw_source.data.source_url,
            offset=0,
            volume=bot.vc_get_status(command.guild_id).volume,
        )
    except RuntimeError:
        return command.response_error("bot not connected to a voice channel")

    return True


class QueueNextCommand(DiscordUserMixin, WebsocketCommand):
    prefix = "queue-next"
    flags = WSCommandFlags.BROADCAST

    async def handle(self):
        rw = await GuildPlaylistAPI.next(self.guild_id)
        if not rw.response.is_success:
            return self.response_error("failed to advance queue", detail=rw.response.json())

        if rw.data and rw.data.current_item:
            result = await _play_current_item(self, rw.data)
            if result is not True:
                return result

        return self.response(playlist=rw.data.model_dump() if rw.data else None)


class QueuePrevCommand(DiscordUserMixin, WebsocketCommand):
    prefix = "queue-prev"
    flags = WSCommandFlags.BROADCAST

    async def handle(self):
        rw = await GuildPlaylistAPI.prev(self.guild_id)
        if not rw.response.is_success:
            return self.response_error("failed to go back in queue", detail=rw.response.json())

        if rw.data and rw.data.current_item:
            result = await _play_current_item(self, rw.data)
            if result is not True:
                return result

        return self.response(playlist=rw.data.model_dump() if rw.data else None)

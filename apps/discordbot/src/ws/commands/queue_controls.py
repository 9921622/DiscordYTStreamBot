from utils.api_backend_wrapper import QueueAPI
from ws.ws_command import WebsocketCommand, WSCommandFlags
from .mixins import DiscordUserMixin


class QueueGetCommand(DiscordUserMixin, WebsocketCommand):
    prefix = "queue-get"

    async def handle(self):
        rw = await QueueAPI.get(self.guild_id)

        if not rw.response.is_success:
            return self.response_error("failed to get queue", detail=rw.response.json())

        return self.response(queue=rw.data.model_dump())


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
        rw = await QueueAPI.add(self.guild_id, self.youtube_id)
        if not rw.response.is_success:
            return self.response_error("failed to add item", detail=rw.response.json())

        rw_queue = await QueueAPI.get(self.guild_id)

        return self.response(queue=rw_queue.data.model_dump())


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
        rw = await QueueAPI.remove(self.guild_id, self.item_id)
        if not rw.response.is_success:
            return self.response_error("failed to remove item", detail=rw.response.json())

        rw_queue = await QueueAPI.get(self.guild_id)

        return self.response(queue=rw_queue.data.model_dump())


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
        rw = await QueueAPI.reorder(self.guild_id, self.order)
        if not rw.response.is_success:
            return self.response_error("failed to reorder queue", detail=rw.response.json())

        rw_queue = await QueueAPI.get(self.guild_id)

        return self.response(queue=rw_queue.data.model_dump())


class QueueClearCommand(DiscordUserMixin, WebsocketCommand):
    prefix = "queue-clear"
    flags = WSCommandFlags.BROADCAST

    async def handle(self):
        rw = await QueueAPI.clear(self.guild_id)

        if not rw.response.is_success:
            return self.response_error("failed to clear queue", detail=rw.response.json())

        return self.response(queue=[])

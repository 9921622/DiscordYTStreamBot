from api.api_backend_wrapper import QueueAPI
from api.websockets.ws_router import WebsocketCommand


class QueueGetCommand(WebsocketCommand):
    prefix = "queue-get"

    async def handle(self):
        rw = await QueueAPI.get(self.guild_id)

        if not rw.response.is_success:
            return self.response_error("failed to get queue", detail=rw.response.json())

        return self.response(queue=rw.data.model_dump())


class QueueAddCommand(WebsocketCommand):
    prefix = "queue-add"
    broadcast = True

    async def handle(self):
        youtube_id = self.data.get("youtube_id")
        if not youtube_id:
            return self.response_error("missing 'youtube_id'")

        rw = await QueueAPI.add(self.guild_id, youtube_id)
        if not rw.response.is_success:
            return self.response_error("failed to add item", detail=rw.response.json())

        rw_queue = await QueueAPI.get(self.guild_id)

        return self.response(queue=rw_queue.data.model_dump())


class QueueRemoveCommand(WebsocketCommand):
    prefix = "queue-remove"
    broadcast = True

    async def handle(self):
        item_id = self.data.get("item_id")
        if item_id is None:
            return self.response_error("missing 'item_id'")

        rw = await QueueAPI.remove(self.guild_id, item_id)
        if not rw.response.is_success:
            return self.response_error("failed to remove item", detail=rw.response.json())

        rw_queue = await QueueAPI.get(self.guild_id)

        return self.response(queue=rw_queue.data.model_dump())


class QueueReorderCommand(WebsocketCommand):
    prefix = "queue-reorder"
    broadcast = True

    async def handle(self):
        order = self.data.get("order")

        if not order or not isinstance(order, list):
            return self.response_error("missing or invalid 'order'")

        rw = await QueueAPI.reorder(self.guild_id, order)
        if not rw.response.is_success:
            return self.response_error("failed to reorder queue", detail=rw.response.json())

        rw_queue = await QueueAPI.get(self.guild_id)

        return self.response(queue=rw_queue.data.model_dump())


class QueueClearCommand(WebsocketCommand):
    prefix = "queue-clear"
    broadcast = True

    async def handle(self):
        rw = await QueueAPI.clear(self.guild_id)

        if not rw.response.is_success:
            return self.response_error("failed to clear queue", detail=rw.response.json())

        return self.response(queue=[])

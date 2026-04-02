import httpx
from api.api_backend_wrapper import QueueAPI
from api.websockets.ws_router import WSRouter

ws = WSRouter()


@ws.command(prefix="queue-get")
async def handle_queue_get(websocket, guild_id: int, data: dict):
    rw = await QueueAPI.get(guild_id)
    if not rw.response.is_success:
        return {"error": "failed to get queue", "detail": rw.response.json()}
    return {"type": "queue-get", "queue": rw.data.model_dump()}


@ws.command(prefix="queue-add", broadcast=True)
async def handle_queue_add(websocket, guild_id: int, data: dict):
    youtube_id = data.get("youtube_id")
    if not youtube_id:
        return {"error": "missing 'youtube_id'"}

    rw = await QueueAPI.add(guild_id, youtube_id)
    if not rw.response.is_success:
        return {"error": "failed to add item", "detail": rw.response.json()}

    rw_queue = await QueueAPI.get(guild_id)
    return {"type": "queue-add", "queue": rw_queue.data.model_dump()}


@ws.command(prefix="queue-remove", broadcast=True)
async def handle_queue_remove(websocket, guild_id: int, data: dict):
    item_id = data.get("item_id")
    if item_id is None:
        return {"error": "missing 'item_id'"}

    rw = await QueueAPI.remove(guild_id, item_id)
    if not rw.response.is_success:
        return {"error": "failed to remove item", "detail": rw.response.json()}

    rw_queue = await QueueAPI.get(guild_id)
    return {"type": "queue-remove", "queue": rw_queue.data.model_dump()}


@ws.command(prefix="queue-reorder", broadcast=True)
async def handle_queue_reorder(websocket, guild_id: int, data: dict):
    order = data.get("order")
    if not order or not isinstance(order, list):
        return {"error": "missing or invalid 'order'"}

    rw = await QueueAPI.reorder(guild_id, order)
    if not rw.response.is_success:
        return {"error": "failed to reorder queue", "detail": rw.response.json()}

    rw_queue = await QueueAPI.get(guild_id)
    return {"type": "queue-reorder", "queue": rw_queue.data.model_dump()}


@ws.command(prefix="queue-clear", broadcast=True)
async def handle_queue_clear(websocket, guild_id: int, data: dict):
    rw = await QueueAPI.clear(guild_id)
    if not rw.response.is_success:
        return {"error": "failed to clear queue", "detail": rw.response.json()}
    return {"type": "queue-clear", "queue": []}

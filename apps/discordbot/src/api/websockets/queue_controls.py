import httpx
from api.api_backend_wrapper import QueueAPI
from api.websockets.ws_router import WSRouter
from api.api_backend_wrapper import guild_queue_url, guild_queue_items_url, guild_queue_item_url, auth_headers

ws = WSRouter()


@ws.command(prefix="queue-get")
async def handle_queue_get(websocket, guild_id: int, data: dict):
    """
    {"type": "queue-get", "guild_id": 123}
    """
    return {"type": "queue-get", "queue": (await QueueAPI.get(guild_id)).json()}


@ws.command(prefix="queue-add", broadcast=True)
async def handle_queue_add(websocket, guild_id: int, data: dict):
    """
    {"type": "queue-add", "guild_id": 123, "youtube_id": "abc"}
    """
    youtube_id = data.get("youtube_id")
    if not youtube_id:
        return {"error": "missing 'youtube_id'"}

    response = await QueueAPI.add(guild_id, youtube_id)
    if response.status_code not in (200, 201):
        return {"error": "failed to add item", "detail": response.json()}

    return {"type": "queue-add", "queue": (await QueueAPI.get(guild_id)).json()}


@ws.command(prefix="queue-remove", broadcast=True)
async def handle_queue_remove(websocket, guild_id: int, data: dict):
    """
    {"type": "queue-remove", "guild_id": 123, "item_id": 42}
    """
    item_id = data.get("item_id")
    if item_id is None:
        return {"error": "missing 'item_id'"}

    response = await QueueAPI.remove(guild_id, item_id)
    if response.status_code not in (200, 204):
        return {"error": "failed to remove item", "detail": response.json()}

    return {"type": "queue-remove", "queue": (await QueueAPI.get(guild_id)).json()}


@ws.command(prefix="queue-reorder", broadcast=True)
async def handle_queue_reorder(websocket, guild_id: int, data: dict):
    """
    {"type": "queue-reorder", "guild_id": 123, "order": [3, 1, 2]}
    """
    order = data.get("order")
    if not order or not isinstance(order, list):
        return {"error": "missing or invalid 'order'"}

    response = await QueueAPI.reorder(guild_id, order)
    if response.status_code != 200:
        return {"error": "failed to reorder queue", "detail": response.json()}

    return {"type": "queue-reorder", "queue": (await QueueAPI.get(guild_id)).json()}


@ws.command(prefix="queue-clear", broadcast=True)
async def handle_queue_clear(websocket, guild_id: int, data: dict):
    """
    {"type": "queue-clear", "guild_id": 123}
    """
    response = await QueueAPI.clear(guild_id)
    if response.status_code not in (200, 204):
        return {"error": "failed to clear queue", "detail": response.json()}

    return {"type": "queue-clear", "queue": []}

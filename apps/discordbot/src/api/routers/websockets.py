from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ws.ws_manager import ws_manager

from ws.ws_commands_router import ws_command_router
import ws.commands  # need to import commands in order to have them enabled

router = APIRouter(prefix="/ws", tags=["ws"])


@router.websocket("/{guild_id}")
async def websocket_endpoint(websocket: WebSocket, guild_id: int):
    guild_id = int(guild_id)
    await ws_manager.connect(guild_id, websocket)
    try:
        while True:
            message = await websocket.receive_json()
            message["guild_id"] = guild_id

            result, guild_broadcast, status_broadcast = await ws_command_router(websocket, message)

            if result:
                await ws_manager.send_one(websocket, guild_id, result)
            if guild_broadcast:
                await ws_manager.send(guild_id, guild_broadcast)
            if status_broadcast:
                await ws_manager.send(guild_id, status_broadcast)

    except WebSocketDisconnect:
        await ws_manager.disconnect(guild_id, websocket)

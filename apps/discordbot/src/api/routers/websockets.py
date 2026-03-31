from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from bot.bot import bot
from bot.ws_manager import ws_manager

from api.websockets.ws_router import ws_command_router


# TODO: move import + initialize to different file???
from api.websockets import debug, voice, music_controls

debug.ws.initialize()
voice.ws.initialize()
music_controls.ws.initialize()


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

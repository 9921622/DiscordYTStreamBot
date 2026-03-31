from fastapi import WebSocket
import asyncio


class WebSocketManager:

    def __init__(self):
        self._connections: dict[int, list[WebSocket]] = {}

    async def connect(self, guild_id: int, websocket: WebSocket):
        await websocket.accept()
        if guild_id not in self._connections:
            self._connections[guild_id] = []
        self._connections[guild_id].append(websocket)

    async def disconnect(self, guild_id: int, websocket: WebSocket):
        sockets = self._connections.get(guild_id, [])
        try:
            sockets.remove(websocket)
        except ValueError:
            pass
        try:
            await websocket.close()
        except Exception:
            pass
        if not sockets:
            self._connections.pop(guild_id, None)

    async def send(self, guild_id: int, data: dict):
        """Send to all connections in a guild."""
        sockets = self._connections.get(guild_id, [])
        dead = []
        for ws in sockets:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            await self.disconnect(guild_id, ws)

    async def send_one(self, websocket: WebSocket, guild_id: int, data: dict):
        """Send to a specific connection only."""
        try:
            await websocket.send_json(data)
        except Exception:
            await self.disconnect(guild_id, websocket)

    def is_connected(self, guild_id: int) -> bool:
        return bool(self._connections.get(guild_id))


ws_manager = WebSocketManager()

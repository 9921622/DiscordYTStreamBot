from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio

from bot.bot import bot
from api.websockets.ws_manager import ws_manager
from settings import settings
from api.routers import misc, admin, voice, debug, websockets


@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(bot.start(settings.DISCORD_TOKEN))
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(misc.router)
app.include_router(voice.router)
app.include_router(admin.router)
app.include_router(debug.router)
app.include_router(websockets.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"hello": "world"}

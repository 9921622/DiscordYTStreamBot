from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
import asyncio

from bot.bot import bot
from settings import settings

from api.routers import misc, music_controls, admin, voice, debug

app = FastAPI()
app.include_router(misc.router)
app.include_router(voice.router)
app.include_router(music_controls.router)
app.include_router(admin.router)
app.include_router(debug.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    asyncio.create_task(bot.start(settings.DISCORD_TOKEN))


@app.get("/")
async def root():
    return {"hello": "world"}

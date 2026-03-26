from fastapi import FastAPI, Depends, Request
import asyncio

from bot.bot import bot
from settings import settings

from api.routers import misc, music_controls, admin

app = FastAPI()
app.include_router(misc.router)
app.include_router(music_controls.router)
app.include_router(admin)


@app.on_event("startup")
async def startup():
    asyncio.create_task(bot.start(settings.DISCORD_TOKEN))


@app.get("/")
async def root():
    return {"hello": "world"}

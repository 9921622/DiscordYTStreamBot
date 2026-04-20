from fastapi import APIRouter, Request
from bot.bot import bot

router = APIRouter(prefix="/voice", tags=["voice"])


@router.get("/connect", name="voice-connect")
async def connect(request: Request, channel_id: int):
    """connect to a voice channel given an id"""
    voice_channel = bot.get_channel(channel_id)
    await bot.vc_connect(voice_channel)
    return {"ok": True}


@router.get("/disconnect", name="voice-disconnect")
async def disconnect(request: Request, guild_id: int):
    """disconnect from a guild"""
    await bot.vc_disconnect(guild_id)
    return {"ok": True}


@router.get("/user-voice-channel", name="voice-user-channel")
async def get_user_voice_channel(request: Request, user_id: int):
    """get the voice channel a user is currently in"""
    for guild in bot.guilds:
        member = guild.get_member(user_id)
        if member and member.voice and member.voice.channel:
            channel = member.voice.channel
            vc = guild.voice_client
            bot_in_same_channel = vc is not None and vc.channel == channel
            return {
                "channel_id": str(channel.id),
                "channel_name": channel.name,
                "guild_id": str(guild.id),
                "guild_name": guild.name,
                "bot_in_channel": bot_in_same_channel,
            }
    return {"channel_id": None}


@router.get("/join-user", name="voice-join-user")
async def join_user_voice_channel(request: Request, user_id: int):
    """join the voice channel a user is currently in"""
    for guild in bot.guilds:
        member = guild.get_member(user_id)
        if member and member.voice and member.voice.channel:
            target_channel = member.voice.channel
            vc = guild.voice_client
            if vc and vc.channel == target_channel:
                return {"ok": False, "error": "Already in that voice channel"}
            await bot.vc_connect(target_channel)
            return {"ok": True}
    return {"ok": False, "error": "User is not in a voice channel"}

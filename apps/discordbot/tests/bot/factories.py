from polyfactory.factories.pydantic_factory import ModelFactory

from bot.models import PlaybackStatus, DiscordUser


class PlaybackStatusFactory(ModelFactory):
    __model__ = PlaybackStatus


class DiscordUserFactory(ModelFactory):
    __model__ = DiscordUser

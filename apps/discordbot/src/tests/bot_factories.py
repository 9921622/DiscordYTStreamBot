from polyfactory.factories.pydantic_factory import ModelFactory
from bot.bot_objects import PlaybackStatus, Member


class PlaybackStatusFactory(ModelFactory):
    __model__ = PlaybackStatus


class MemberFactory(ModelFactory):
    __model__ = Member

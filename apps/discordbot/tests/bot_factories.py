from polyfactory.factories.pydantic_factory import ModelFactory

from bot.models import PlaybackStatus, Member


class PlaybackStatusFactory(ModelFactory):
    __model__ = PlaybackStatus


class MemberFactory(ModelFactory):
    __model__ = Member

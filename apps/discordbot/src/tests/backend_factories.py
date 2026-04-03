from polyfactory.factories.pydantic_factory import ModelFactory
from utils.api_backend_wrapper import (
    YoutubeVideoSchema,
    VideoSourceSchema,
    DiscordUserSchema,
    GuildQueueItemSchema,
    GuildQueueSchema,
)


class YoutubeVideoSchemaFactory(ModelFactory):
    __model__ = YoutubeVideoSchema
    source_url = "https://example.com/audio.mp3"


class VideoSourceSchemaFactory(ModelFactory):
    __model__ = VideoSourceSchema
    source_url = "https://example.com/audio.mp3"


class DiscordUserSchemaFactory(ModelFactory):
    __model__ = DiscordUserSchema


class GuildQueueItemSchemaFactory(ModelFactory):
    __model__ = GuildQueueItemSchema
    video = YoutubeVideoSchemaFactory.build


class GuildQueueSchemaFactory(ModelFactory):
    __model__ = GuildQueueSchema
    items = lambda: [GuildQueueItemSchemaFactory.build()]

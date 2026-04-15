from polyfactory.factories.pydantic_factory import ModelFactory

from utils.api_backend_wrapper import (
    YoutubeVideoSchema,
    VideoSourceSchema,
    DiscordUserSchema,
    GuildPlaylistItemSchema,
    GuildPlaylistSchema,
)


class YoutubeVideoSchemaFactory(ModelFactory):
    __model__ = YoutubeVideoSchema
    source_url = "https://example.com/audio.mp3"


class VideoSourceSchemaFactory(ModelFactory):
    __model__ = VideoSourceSchema
    source_url = "https://example.com/audio.mp3"


class DiscordUserSchemaFactory(ModelFactory):
    __model__ = DiscordUserSchema


class GuildPlaylistItemSchemaFactory(ModelFactory):
    __model__ = GuildPlaylistItemSchema
    video = YoutubeVideoSchemaFactory.build


class GuildPlaylistSchemaFactory(ModelFactory):
    __model__ = GuildPlaylistSchema
    current_item = GuildPlaylistItemSchemaFactory.build
    items = lambda: [GuildPlaylistItemSchemaFactory.build()]

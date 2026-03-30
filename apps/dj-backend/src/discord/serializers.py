from rest_framework import serializers
from discord.models import DiscordGuild, GuildQueue, GuildQueueItem
from youtube.serializers import YoutubeVideoSerializer


class DiscordGuildSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscordGuild
        fields = ["guild_id", "name"]


class GuildQueueItemSerializer(serializers.ModelSerializer):
    video = YoutubeVideoSerializer(read_only=True)

    class Meta:
        model = GuildQueueItem
        fields = ["id", "video", "order", "added_by", "added_at"]


class GuildQueueSerializer(serializers.ModelSerializer):
    items = GuildQueueItemSerializer(many=True, read_only=True)

    class Meta:
        model = GuildQueue
        fields = ["id", "guild", "items", "created_at", "updated_at"]

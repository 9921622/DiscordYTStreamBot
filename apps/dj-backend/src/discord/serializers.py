from rest_framework import serializers
from discord.models import DiscordUser, DiscordGuild, GuildPlaylist, GuildPlaylistItem
from youtube.serializers import YoutubeVideoSerializer


class DiscordUserSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = DiscordUser
        fields = ["discord_id", "global_name", "avatar_url"]

    def get_avatar_url(self, obj):
        return obj.get_avatar_uri()


class DiscordGuildSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscordGuild
        fields = ["guild_id", "name"]


class GuildPlaylistItemSerializer(serializers.ModelSerializer):
    video = YoutubeVideoSerializer(read_only=True)
    added_by = DiscordUserSerializer(read_only=True)

    class Meta:
        model = GuildPlaylistItem
        fields = ["id", "video", "order", "added_by", "added_at"]


class GuildPlaylistSerializer(serializers.ModelSerializer):
    items = GuildPlaylistItemSerializer(many=True, read_only=True)
    current_item = GuildPlaylistItemSerializer(read_only=True)

    class Meta:
        model = GuildPlaylist
        fields = ["id", "guild", "current_item", "items", "created_at", "updated_at"]

from rest_framework import serializers
from .models import YoutubeVideo, YoutubePlaylist, YoutubePlaylistItem, YoutubeTag


class YoutubeTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = YoutubeTag
        fields = ["name"]


class YoutubeVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = YoutubeVideo
        fields = ["youtube_id", "title", "creator", "source_url", "duration", "thumbnail", "created_at", "tags"]

    tags = serializers.SlugRelatedField(many=True, read_only=True, slug_field="name")


class YoutubePlaylistItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = YoutubePlaylistItem
        fields = ["id", "video", "order", "added_at"]

    video = YoutubeVideoSerializer(read_only=True)


class YoutubePlaylistSerializer(serializers.ModelSerializer):
    class Meta:
        model = YoutubePlaylist
        fields = ["id", "name", "user", "youtube_playlist_id", "items", "created_at", "updated_at"]

    items = YoutubePlaylistItemSerializer(many=True, read_only=True)
    user = serializers.StringRelatedField(read_only=True)

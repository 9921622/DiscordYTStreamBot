from rest_framework import serializers
from .models import YoutubeVideo, YoutubePlaylist, YoutubePlaylistItem


class YoutubeVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = YoutubeVideo
        fields = ["youtube_id", "title", "creator", "source_url", "duration", "thumbnail", "created_at"]


class YoutubePlaylistItemSerializer(serializers.ModelSerializer):
    video = YoutubeVideoSerializer(read_only=True)

    class Meta:
        model = YoutubePlaylistItem
        fields = ["id", "video", "order", "added_at"]


class YoutubePlaylistSerializer(serializers.ModelSerializer):
    items = YoutubePlaylistItemSerializer(many=True, read_only=True)
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = YoutubePlaylist
        fields = ["id", "name", "user", "youtube_playlist_id", "items", "created_at", "updated_at"]

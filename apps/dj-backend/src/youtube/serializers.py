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
        fields = ["title", "owned_by", "youtube_playlist_id", "items", "created_at", "updated_at", "playlist_type"]
        read_only_fields = ["owned_by", "created_at"]

    items = YoutubePlaylistItemSerializer(many=True, read_only=True)
    owned_by = serializers.StringRelatedField(read_only=True)
    playlist_type = serializers.ChoiceField(
        choices=YoutubePlaylist.PlaylistType.choices,
        default=YoutubePlaylist.PlaylistType.PUBLIC,
    )

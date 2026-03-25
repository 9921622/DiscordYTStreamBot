from django.db import models

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from youtube.models import YoutubeVideo, YoutubePlaylist, YoutubePlaylistItem
from youtube.serializers import YoutubeVideoSerializer, YoutubePlaylistSerializer


class YoutubeVideoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API to list or retrieve cached YouTube videos.
    """

    queryset = YoutubeVideo.objects.all()
    serializer_class = YoutubeVideoSerializer
    lookup_field = "youtube_id"


class YoutubePlaylistViewSet(viewsets.ModelViewSet):
    """
    API for managing user playlists.
    """

    queryset = YoutubePlaylist.objects.all()
    serializer_class = YoutubePlaylistSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"])
    def add_video(self, request, pk=None):
        """
        Add a video to the playlist.
        """
        playlist = self.get_object()
        youtube_id = request.data.get("youtube_id")
        if not youtube_id:
            return Response({"error": "youtube_id required"}, status=status.HTTP_400_BAD_REQUEST)

        video, _ = YoutubeVideo.objects.get_or_create(youtube_id=youtube_id)
        # Determine order automatically
        last_order = playlist.items.aggregate(models.Max("order"))["order__max"] or 0
        item = YoutubePlaylistItem.objects.create(playlist=playlist, video=video, order=last_order + 1)
        return Response({"id": item.id, "order": item.order})

from django.db import models
from django.http import Http404

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from youtube.models import YoutubeVideo, YoutubePlaylist, YoutubePlaylistItem
from youtube.serializers import YoutubeVideoSerializer, YoutubePlaylistSerializer


class YoutubeVideoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API to list or retrieve cached YouTube videos.
    If a video is not found, it will automatically fetch and cache it from YouTube.
    """

    queryset = YoutubeVideo.objects.all()
    serializer_class = YoutubeVideoSerializer
    lookup_field = "youtube_id"

    def retrieve(self, request, *args, **kwargs):
        """
        Override retrieve to auto-fetch videos from YouTube if not in cache.
        """
        youtube_id = kwargs.get(self.lookup_field)

        try:
            # Try to get from database
            return super().retrieve(request, *args, **kwargs)
        except Http404:
            # If not found, fetch from YouTube and create it
            try:
                youtube_url = YoutubeVideo.URL_TEMPLATE.format(youtube_id=youtube_id)
                video = YoutubeVideo.from_url(youtube_url, save=True)
                serializer = self.get_serializer(video)
                return Response(serializer.data)
            except Exception as e:
                return Response(
                    {"error": f"Failed to fetch video from YouTube: {str(e)}"}, status=status.HTTP_404_NOT_FOUND
                )


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

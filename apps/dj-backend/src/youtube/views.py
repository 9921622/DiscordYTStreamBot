from django.db import models
from django.http import Http404

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

import yt_dlp

from youtube.models import YoutubeVideo, YoutubePlaylist, YoutubePlaylistItem
from youtube.services import YouTubeService
from youtube.serializers import YoutubeVideoSerializer, YoutubePlaylistSerializer


class YoutubeVideoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API to list or retrieve cached YouTube videos.
    If a video is not found, it will automatically fetch and cache it.
    """

    queryset = YoutubeVideo.objects.all()
    serializer_class = YoutubeVideoSerializer
    lookup_field = "youtube_id"

    # ----------------------------------------
    # retrieve
    # ----------------------------------------
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
                video = YouTubeService.fetch_and_cache_video(youtube_id)
                serializer = self.get_serializer(video)
                return Response(serializer.data)

            except Exception as e:
                return Response(
                    {"error": f"Failed to fetch video from YouTube: {str(e)}"},
                    status=status.HTTP_404_NOT_FOUND,
                )

    # ----------------------------------------
    # get_source
    # ----------------------------------------
    @action(detail=True, methods=["get"], url_path="get-source")
    def get_source(self, request, youtube_id=None):
        """Get the streamable source URL for a video, auto-fetching if not cached."""
        try:
            video = YoutubeVideo.objects.get(youtube_id=youtube_id)

        except YoutubeVideo.DoesNotExist:
            try:
                video = YouTubeService.fetch_and_cache_video(youtube_id)
                return Response({"source_url": video.source_url})

            except Exception as e:
                return Response(
                    {"error": f"Failed to fetch video from YouTube: {str(e)}"},
                    status=status.HTTP_404_NOT_FOUND,
                )

        try:
            source_url = YouTubeService.get_source_url(video.get_url())
            return Response({"source_url": source_url})

        except Exception as e:
            return Response(
                {"error": f"Failed to extract source URL: {str(e)}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )


class YoutubePlaylistViewSet(viewsets.ModelViewSet):
    """
    API for managing user playlists.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    queryset = YoutubePlaylist.objects.all()
    serializer_class = YoutubePlaylistSerializer

    def perform_create(self, serializer):
        serializer.save(owned_by=self.request.user)

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


class YoutubeSearchView(APIView):
    """
    Search for YouTube videos.
    GET /api/youtube/search/?q=<query>&max_results=<count>
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Search YouTube for videos.
        Query parameters:
            - q: search query (required)
            - max_results: maximum number of results (default: 10, max: 50)
        """
        query = request.query_params.get("q")
        max_results = int(request.query_params.get("max_results", 10))

        if not query:
            return Response(
                {"error": "Query parameter 'q' is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            results = YouTubeService.search(query, max_results)

            return Response(
                {
                    "query": query,
                    "results": results,
                }
            )

        except Exception as e:
            return Response(
                {"error": f"Failed to search YouTube: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

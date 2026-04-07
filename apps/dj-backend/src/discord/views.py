from django.shortcuts import render, redirect, reverse
from django.views import View
from django.http import JsonResponse
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User
from django.db import models

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from backend.mixins import RefreshTokenMixin
from backend.permissions import IsInternalService
from discord.api import DiscordAPIClient, DiscordCDNAPI
from discord.models import DiscordUser, DiscordGuild, GuildPlaylistManager, GuildPlaylist, GuildPlaylistItem
from discord.serializers import (
    DiscordUserSerializer,
    DiscordGuildSerializer,
    GuildPlaylistSerializer,
    GuildPlaylistItemSerializer,
)
from youtube.services import YouTubeService
from youtube.models import YoutubeVideo

import requests
from urllib.parse import urlparse, urlencode, parse_qs, urlunparse
from datetime import timedelta


def get_oauth_redirect(request):
    """Returns the absolute URI for the Discord OAuth callback endpoint.

    This function exists as a single source of truth for the redirect_uri used
    in both the OAuth authorization request (DiscordOAuth) and the token exchange
    request (DiscordLogin.exchange_code).

    Security:
        Discord requires that the redirect_uri in the token exchange request
        exactly matches the one used in the original authorization request.
        This prevents authorization code interception attacks — if an attacker
        captures the ?code= from the redirect, they cannot exchange it for a
        token without also knowing (and being able to use) the exact redirect_uri
        that was registered and sent in the original request.

        By deriving the URI dynamically from the request, we also ensure it is
        always correct across environments (local, staging, production) without
        hardcoding URLs, avoiding misconfiguration where a hardcoded URI could
        point to the wrong environment and silently succeed or fail.
    """
    # https://docs.discord.com/developers/topics/oauth2#authorization-code-grant
    # request.build_absolute_uri() would return the internal Docker hostname (dj-backend:8000)
    # which Discord cannot reach — use the public-facing BACKEND_URL instead
    path = reverse("discord:login")
    return request.build_absolute_uri(path)


class DiscordUserCreateUpdateMixin:
    model = DiscordUser

    def create_or_update_user(self, token_data: dict, user_data: dict) -> DiscordUser:
        expires_at = timezone.now() + timedelta(seconds=token_data["expires_in"])

        dj_user, _ = User.objects.get_or_create(username=user_data["id"])
        disc_user, _ = self.model.objects.update_or_create(
            discord_id=user_data["id"],
            defaults={
                "user": dj_user,
                "username": user_data["username"],
                "global_name": user_data.get("global_name"),
                "avatar": user_data.get("avatar"),
                "access_token": token_data["access_token"],
                "refresh_token": token_data["refresh_token"],
                "token_expires_at": expires_at,
                "scope": token_data["scope"],
            },
        )
        return disc_user


class DiscordLoginView(View, DiscordUserCreateUpdateMixin, RefreshTokenMixin):
    OAUTH2_TOKEN_ENDPOINT = "https://discord.com/api/oauth2/token"

    def dispatch(self, request, **kwargs):
        self.code = request.GET.get("code")
        return super().dispatch(request, **kwargs)

    def get(self, request, *args, **kwargs):
        if not self.code:
            return redirect(reverse("discord:oauth"))

        # oauth + create user
        token_data = self.get_exchange_data()
        user_data = DiscordAPIClient(token_data["access_token"]).get_current_user()

        discord_user = self.create_or_update_user(token_data, user_data)

        tokens = self.get_tokens_for_user(discord_user.user)
        #
        params = urlencode({"access": tokens["access"], "refresh": tokens["refresh"]})
        return redirect(f"{settings.FRONTEND_URL}/auth/callback?{params}")

    def get_exchange_data(self):
        """
        https://docs.discord.com/developers/topics/oauth2
        returns
            {
            "access_token": "6qrZcUqja7812RVdnEKjpzOL4CvHBFG",
            "token_type": "Bearer",
            "expires_in": 604800,
            "scope": "identify connections"
            }
        """
        data = {
            "client_id": settings.DISCORD_CLIENT_ID,
            "client_secret": settings.DISCORD_CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": self.code,
            "redirect_uri": get_oauth_redirect(self.request),
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        response = requests.post(self.OAUTH2_TOKEN_ENDPOINT, data=data, headers=headers)
        print("STATUS:", response.status_code)
        print("BODY:", response.text)
        response.raise_for_status()
        return response.json()


class DiscordOAuthView(View):

    OAUTH2_AUTHORIZE_ENDPOINT = "https://discord.com/oauth2/authorize"
    SCOPES = ["identify"]

    def get(self, request, *args, **kwargs):
        return redirect(self.build_oauth_url(request))

    def build_oauth_url(self, request):
        params = {
            "client_id": settings.DISCORD_CLIENT_ID,
            "response_type": "code",
            "scope": " ".join(self.SCOPES),
            "redirect_uri": get_oauth_redirect(request),
        }
        return f"{self.OAUTH2_AUTHORIZE_ENDPOINT}?{urlencode(params)}"


class DiscordProfileView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        discord_user = request.user.discord
        return Response(DiscordUserSerializer(discord_user).data)


class DiscordUserView(APIView):
    authentication_classes = []
    permission_classes = [IsInternalService]

    def get(self, request, user_id: str):
        discord_user = DiscordUser.objects.get(discord_id=user_id)
        return Response(DiscordUserSerializer(discord_user).data)


class DiscordGuildView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, guild_id: str):
        """Get a guild by ID"""
        try:
            guild = DiscordGuild.objects.get(guild_id=guild_id)
            return Response(DiscordGuildSerializer(guild).data)
        except DiscordGuild.DoesNotExist:
            return Response({"error": "Guild not found"}, status=404)


class GuildPlaylistView(APIView):
    authentication_classes = []
    permission_classes = [IsInternalService]

    def get(self, request, guild_id: str):
        """Get the current queue for a guild."""
        queue = GuildPlaylist.objects.get_playlist(guild_id)
        return Response(GuildPlaylistSerializer(queue).data)

    def delete(self, request, guild_id: str):
        """Clear the queue."""
        GuildPlaylist.objects.clear(guild_id)
        queue = GuildPlaylist.objects.get_playlist(guild_id)
        return Response(GuildPlaylistSerializer(queue).data)


class GuildPlaylistAddSongView(APIView):
    authentication_classes = []
    permission_classes = [IsInternalService]

    def patch(self, request, guild_id: str):
        """Add a video to the queue. Expects { youtube_id, discord_id }."""
        youtube_id = request.data.get("youtube_id")
        if not youtube_id:
            return Response({"error": "youtube_id required"}, status=400)

        discord_id = request.data.get("discord_id")
        if not discord_id:
            return Response({"error": "discord_id required"}, status=400)

        try:
            added_by = DiscordUser.objects.get(discord_id=discord_id)
        except DiscordUser.DoesNotExist:
            return Response({"error": "User has not authenticated with the web app"}, status=403)

        try:
            GuildPlaylist.objects.add_item(guild_id, youtube_id, added_by=added_by)
        except YoutubeVideo.DoesNotExist:
            try:
                GuildPlaylist.objects.add_item(guild_id, youtube_id, added_by=added_by, fetch=True)
            except Exception as e:
                return Response({"error": f"Failed to fetch video from YouTube: {str(e)}"}, status=502)

        queue = GuildPlaylist.objects.get_playlist(guild_id)
        return Response(GuildPlaylistSerializer(queue).data, status=201)


class GuildPlaylistRemoveSongView(APIView):
    authentication_classes = []
    permission_classes = [IsInternalService]

    def patch(self, request, guild_id: str):
        """Remove a specific item from the queue. Expects { item_id }."""
        item_id = request.data.get("item_id")
        if not item_id:
            return Response({"error": "item_id required"}, status=400)

        try:
            GuildPlaylist.objects.remove_item(guild_id, item_id)
        except GuildPlaylistItem.DoesNotExist:
            return Response({"error": "Item not found"}, status=404)

        queue = GuildPlaylist.objects.get_playlist(guild_id)
        return Response(GuildPlaylistSerializer(queue).data, status=200)


class GuildPlaylistNextView(APIView):
    authentication_classes = []
    permission_classes = [IsInternalService]

    def get_data(self, request):
        self.item_id = request.data.get("item_id")
        self.video_id = request.data.get("video_id")
        self.discord_id = request.data.get("discord_id")

    def patch(self, request, guild_id: str):
        """
        Advance to the next item.
        - item_id in body: sets that PlaylistItem as current (unambiguous, preferred)
        - video_id in body: sets next item by YoutubeVideo lookup
        - discord_id: goes with video id
        - neither: advances to the natural next item in order
        """
        self.get_data(request)
        if self.item_id is not None and (self.video_id is not None or self.discord_id is not None):
            return Response({"error": "if item_id is provided, video and user must be None"}, status=404)

        # if item_id is populated
        # the item exists in the playlist and is being moved to be the playing video
        if self.item_id:
            try:
                playlist_item = GuildPlaylistItem.objects.get(id=self.item_id, playlist__guild__guild_id=guild_id)
            except GuildPlaylistItem.DoesNotExist:
                return Response({"error": f"Item {self.item_id} not found"}, status=404)
            item = GuildPlaylist.objects.next_item(guild_id, playlist_item=playlist_item)

        # if video_id and discord_id is populated
        # the item is being put into the playlist and being set as the current song playing.
        elif self.video_id and self.discord_id:
            video = YouTubeService.get_or_fetch(self.video_id)
            try:
                discord_user = DiscordUser.objects.get(discord_id=self.discord_id)
            except DiscordUser.DoesNotExist:
                return Response({"error": f"DiscordUser {self.discord_id} not found"}, status=404)

            item = GuildPlaylist.objects.next_item_as_video(guild_id, video=video, added_by=discord_user)

        # default.
        # returns the next item
        else:
            item = GuildPlaylist.objects.next_item(guild_id)

        queue = GuildPlaylist.objects.get_playlist(guild_id)
        return Response(GuildPlaylistSerializer(queue).data)


class GuildPlaylistPrevView(APIView):
    authentication_classes = []
    permission_classes = [IsInternalService]

    def patch(self, request, guild_id: str):
        """Move to the previous item."""
        GuildPlaylist.objects.prev_item(guild_id)
        queue = GuildPlaylist.objects.get_playlist(guild_id)
        return Response(GuildPlaylistSerializer(queue).data)


class GuildPlaylistReorderView(APIView):
    authentication_classes = []
    permission_classes = [IsInternalService]

    def patch(self, request, guild_id: str):
        """Reorder queue items. Expects { "order": [item_id, item_id, ...] }."""
        item_ids = request.data.get("order")
        if not item_ids or not isinstance(item_ids, list):
            return Response({"error": "order must be a list of item IDs"}, status=400)

        try:
            GuildPlaylist.objects.reorder_items(guild_id, item_ids)
        except ValueError as e:
            return Response({"error": str(e)}, status=400)

        queue = GuildPlaylist.objects.get_playlist(guild_id)
        return Response(GuildPlaylistSerializer(queue).data, status=200)

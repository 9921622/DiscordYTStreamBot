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
from discord.models import DiscordUser, DiscordGuild, GuildQueueManager, GuildQueue, GuildQueueItem
from discord.serializers import (
    DiscordGuildSerializer,
    GuildQueueSerializer,
    GuildQueueItemSerializer,
)
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

    # if using non docker. just change the backend url
    from django.conf import settings

    path = reverse("discord:login")
    return f"{settings.BACKEND_URL}{path}"


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
        return Response(
            {
                "discord_id": discord_user.discord_id,
                "username": discord_user.username,
                "global_name": discord_user.global_name,
                "avatar": discord_user.get_avatar_uri(),
            }
        )


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


class GuildQueueView(APIView):
    authentication_classes = []
    permission_classes = [IsInternalService]

    def get(self, request, guild_id: str):
        """Get the current queue for a guild"""
        queue = GuildQueue.objects.get_for_guild(guild_id)
        return Response(GuildQueueSerializer(queue).data)

    def delete(self, request, guild_id: str):
        """Clear the queue"""
        queue = GuildQueue.objects.get_for_guild(guild_id)
        queue.clear()
        return Response({"ok": True})


class GuildQueueItemView(APIView):
    authentication_classes = []
    permission_classes = [IsInternalService]

    def post(self, request, guild_id: str):
        """Add a video to the queue"""
        youtube_id = request.data.get("youtube_id")
        if not youtube_id:
            return Response({"error": "youtube_id required"}, status=400)

        try:
            item = GuildQueue.objects.add_item(guild_id, youtube_id)
        except YoutubeVideo.DoesNotExist:
            try:
                item = GuildQueue.objects.add_item(guild_id, youtube_id, fetch=True)
            except Exception as e:
                return Response({"error": f"Failed to fetch video from YouTube: {str(e)}"}, status=502)

        return Response(GuildQueueItemSerializer(item).data, status=201)

    def delete(self, request, guild_id: str, item_id: int):
        """Remove a specific item from the queue"""
        try:
            GuildQueue.objects.remove_item(guild_id, item_id)
            return Response({"ok": True})
        except GuildQueueItem.DoesNotExist:
            return Response({"error": "Item not found"}, status=404)

    def patch(self, request, guild_id: str):
        """Reorder queue items. Expects { "order": [item_id, item_id, ...] }"""
        item_ids = request.data.get("order")
        if not item_ids or not isinstance(item_ids, list):
            return Response({"error": "order must be a list of item IDs"}, status=400)

        try:
            GuildQueue.objects.reorder_items(guild_id, item_ids)
        except ValueError as e:
            return Response({"error": str(e)}, status=400)

        return Response({"ok": True})

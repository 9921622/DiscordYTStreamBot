from django.db import models
from django.contrib.auth.models import User

from discord.api import DiscordCDNAPI


class DiscordUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="discord")
    discord_id = models.CharField(max_length=64, unique=True, primary_key=True)

    username = models.CharField(max_length=64)
    global_name = models.CharField(max_length=64, null=True, blank=True)
    avatar = models.CharField(max_length=256, null=True, blank=True)

    access_token = models.CharField(max_length=256)
    refresh_token = models.CharField(max_length=256)
    token_expires_at = models.DateTimeField()

    scope = models.CharField(max_length=256)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.username} ({self.discord_id})"

    def get_avatar_uri(self):
        return DiscordCDNAPI.build_avatar_url(self.discord_id, self.avatar)

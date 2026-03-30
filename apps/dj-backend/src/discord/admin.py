from django.contrib import admin
from .models import DiscordUser


@admin.register(DiscordUser)
class DiscordUserAdmin(admin.ModelAdmin):
    list_display = ["discord_id", "username", "global_name", "token_expires_at", "created_at"]
    search_fields = ["discord_id", "username", "global_name"]
    readonly_fields = [
        "discord_id",
        "created_at",
        "updated_at",
        "access_token",
        "refresh_token",
        "token_expires_at",
        "scope",
    ]

    fieldsets = [
        ["User", {"fields": ["discord_id", "username", "global_name", "avatar"]}],
        ["Token", {"fields": ["access_token", "refresh_token", "token_expires_at", "scope"]}],
        ["Timestamps", {"fields": ["created_at", "updated_at"]}],
    ]

from django.contrib import admin
from .models import DiscordUser, DiscordGuild, GuildQueue, GuildQueueItem


@admin.register(DiscordUser)
class DiscordUserAdmin(admin.ModelAdmin):
    list_display = [
        "discord_id",
        "username",
        "global_name",
        "token_expires_at",
        "created_at",
    ]
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
        [
            "Token",
            {"fields": ["access_token", "refresh_token", "token_expires_at", "scope"]},
        ],
        ["Timestamps", {"fields": ["created_at", "updated_at"]}],
    ]


@admin.register(DiscordGuild)
class DiscordGuildAdmin(admin.ModelAdmin):
    list_display = ["guild_id", "name"]
    search_fields = ["guild_id", "name"]


class GuildQueueItemInline(admin.TabularInline):
    model = GuildQueueItem
    extra = 0
    autocomplete_fields = ["video", "added_by"]
    ordering = ["order"]


@admin.register(GuildQueue)
class GuildQueueAdmin(admin.ModelAdmin):
    list_display = ["guild", "created_at", "updated_at", "queue_length"]
    search_fields = ["guild__name", "guild__guild_id"]
    readonly_fields = ["created_at", "updated_at"]
    inlines = [GuildQueueItemInline]

    def queue_length(self, obj):
        return obj.items.count()

    queue_length.short_description = "Items"


@admin.register(GuildQueueItem)
class GuildQueueItemAdmin(admin.ModelAdmin):
    list_display = ["video", "queue", "order", "added_by", "added_at"]
    search_fields = [
        "video__title",
        "queue__guild__name",
        "queue__guild__guild_id",
        "added_by__username",
    ]
    list_filter = ["queue__guild"]
    autocomplete_fields = ["video", "queue", "added_by"]
    ordering = ["queue", "order"]
    readonly_fields = ["added_at"]

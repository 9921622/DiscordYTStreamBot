from django.contrib import admin

from youtube.models import YoutubeTag, YoutubeVideo, YoutubePlaylist, YoutubePlaylistItem


@admin.register(YoutubeTag)
class YoutubeTagAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]
    ordering = ["name"]


@admin.register(YoutubeVideo)
class YoutubeVideoAdmin(admin.ModelAdmin):
    list_display = ["youtube_id", "title", "creator", "duration", "created_at"]
    list_filter = ["created_at", "creator"]
    search_fields = ["youtube_id", "title", "creator"]
    readonly_fields = ["youtube_id", "created_at"]
    filter_horizontal = ["tags"]
    ordering = ["-created_at"]


@admin.register(YoutubePlaylist)
class YoutubePlaylistAdmin(admin.ModelAdmin):
    list_display = ["title", "youtube_playlist_id", "owned_by", "created_at"]
    list_filter = ["created_at", "owned_by"]
    search_fields = ["title", "youtube_playlist_id", "owned_by__username"]
    readonly_fields = ["created_at", "updated_at"]
    ordering = ["-created_at"]


@admin.register(YoutubePlaylistItem)
class YoutubePlaylistItemAdmin(admin.ModelAdmin):
    list_display = ["playlist", "video", "order"]
    list_filter = ["playlist", "order"]
    search_fields = ["playlist__name", "video__title"]
    ordering = ["playlist", "order"]

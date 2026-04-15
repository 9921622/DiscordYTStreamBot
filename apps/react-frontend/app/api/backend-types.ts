import type { YoutubeVideo } from "./youtube/youtube-types";


export interface WSResponse {
    type: string;
    success: boolean;
    data?: Record<string, any>;
    error?: { message: string; detail?: Record<string, any> };
}

export interface DiscordUser {
    discord_id : string;
    username : string;
    global_name : string;
    avatar_url : string;
}
export interface DiscordGuildPlaylistItem {
    id: number
    video: YoutubeVideo
    order: number
    added_by: DiscordUser | null
    added_at: string
}

export interface DiscordGuildPlaylist {
    id: number
    guild: string
    current_item : DiscordGuildPlaylistItem
    items: DiscordGuildPlaylistItem[]
    created_at: string
    updated_at: string
}

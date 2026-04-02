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
    avatar : string;
}
export interface DiscordGuildQueueItem {
    id: number
    video: YoutubeVideo
    order: number
    added_by: string | null
    added_at: string
}

export interface DiscordGuildQueue {
    id: number
    guild: string
    items: DiscordGuildQueueItem[]
    created_at: string
    updated_at: string
}

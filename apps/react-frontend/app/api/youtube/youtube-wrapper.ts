import axios from "axios";

import type {
  YoutubePlaylist,
  YoutubePlaylistItem,
  YoutubeVideo,
} from "./youtube-types";


export function extractYoutubeId(url: string): string | null {
  try {
    // Match youtu.be format: https://youtu.be/ID or youtu.be/ID
    const shortMatch = url.match(/youtu\.be\/([a-zA-Z0-9_-]{11})/);
    if (shortMatch) return shortMatch[1];

    // Match youtube.com format: v=ID parameter
    const urlObj = new URL(url.startsWith("http") ? url : `https://${url}`);
    const videoId = urlObj.searchParams.get("v");
    if (videoId && videoId.length === 11) return videoId;

    return null;
  } catch {
    return null;
  }
}

class YoutubeVideoAPI {
  private baseURL: string;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  async list(params?: Record<string, any>): Promise<YoutubeVideo[]> {
    // Get all YouTube videos with optional query filters
    try {
      const response = await axios.get<YoutubeVideo[]>(`${this.baseURL}/`, { params });
      return response.data;
    } catch (error) {
      throw new Error("Failed to fetch videos");
    }
  }

  async retrieve(youtubeId: string): Promise<YoutubeVideo> {
    // Get a specific video by youtube_id
    try {
      const response = await axios.get<YoutubeVideo>(`${this.baseURL}/${youtubeId}/`);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to fetch video (${this.baseURL}/${youtubeId}/): ${youtubeId}`);
    }
  }
}


class YoutubePlaylistAPI {
  private baseURL: string;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  async list(params?: Record<string, any>): Promise<YoutubePlaylist[]> {
    // Get all playlists with optional query filters
    try {
      const response = await axios.get<YoutubePlaylist[]>(`${this.baseURL}/`, { params });
      return response.data;
    } catch (error) {
      throw new Error("Failed to fetch playlists");
    }
  }

  async retrieve(playlistId: number): Promise<YoutubePlaylist> {
    // Get a specific playlist by id
    try {
      const response = await axios.get<YoutubePlaylist>(`${this.baseURL}/${playlistId}/`);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to fetch playlist: ${playlistId}`);
    }
  }

  async create(data: {
    name: string;
    playlist_type?: string;
  }): Promise<YoutubePlaylist> {
    // Create a new playlist
    try {
      const response = await axios.post<YoutubePlaylist>(`${this.baseURL}/`, data);
      return response.data;
    } catch (error) {
      throw new Error("Failed to create playlist");
    }
  }

  async update(
    playlistId: number,
    data: Partial<YoutubePlaylist>
  ): Promise<YoutubePlaylist> {
    // Update a playlist
    try {
      const response = await axios.patch<YoutubePlaylist>(`${this.baseURL}/${playlistId}/`, data);
      return response.data;
    } catch (error) {
      throw new Error("Failed to update playlist");
    }
  }

  async delete(playlistId: number): Promise<void> {
    // Delete a playlist
    try {
      await axios.delete(`${this.baseURL}/${playlistId}/`);
    } catch (error) {
      throw new Error("Failed to delete playlist");
    }
  }

  async addVideo(
    playlistId: number,
    youtubeId: string
  ): Promise<YoutubePlaylistItem> {
    // Add a video to a playlist (custom action)
    try {
      const response = await axios.post<YoutubePlaylistItem>(
        `${this.baseURL}/${playlistId}/add_video/`,
        { youtube_id: youtubeId }
      );
      return response.data;
    } catch (error) {
      throw new Error("Failed to add video to playlist");
    }
  }
}



class YoutubeAPI {
  public video: YoutubeVideoAPI;
  public playlist: YoutubePlaylistAPI;

  constructor() {
    const baseURL = `${import.meta.env.VITE_API_URL}/youtube`;
    this.video = new YoutubeVideoAPI(`${baseURL}/videos`);
    this.playlist = new YoutubePlaylistAPI(`${baseURL}/playlists`);
  }
}

export const youtubeAPI = new YoutubeAPI();

import axios from "axios";
import { stringify } from "../../utils/misc";

import type { YoutubePlaylist, YoutubePlaylistItem, YoutubeVideo } from "./youtube-types";








class _YoutubeAPI_VIDEO_MODEL {
  private baseURL: string;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  async getVideos(params?: Record<string, any>): Promise<YoutubeVideo[]> {
    // Get all YouTube videos with optional query filters
    try {

      const query = params ? `?${stringify(params)}` : "";
      const response = await axios.get(`${this.baseURL}/${query}`);
      return response.data;

    } catch (error) {
      throw new Error("Failed to fetch videos");
    }
  }

  async getVideo(youtubeId: string): Promise<YoutubeVideo> {
    // Get a specific video by youtube_id
    try {

      const response = await axios.get(`${this.baseURL}/${youtubeId}/`);
      return response.data;

    } catch (error) {
      throw new Error(`Failed to fetch video: ${youtubeId}`);
    }
  }
}

class _YoutubeAPI_PLAYLIST_MODEL {
  private baseURL: string;

  constructor(baseURL : string) {
    this.baseURL = baseURL;
  }

}

class YoutubeAPI {
  public youtubeVideo : _YoutubeAPI_VIDEO_MODEL;
  public youtubePlaylist : _YoutubeAPI_PLAYLIST_MODEL;


  constructor() {
    const baseURL = `${import.meta.env.VITE_API_URL}/youtube`;
    this.youtubeVideo = new _YoutubeAPI_VIDEO_MODEL(baseURL + "/videos");
    this.youtubePlaylist = new _YoutubeAPI_PLAYLIST_MODEL(baseURL + "/playlists");
  }

}
export const youtubeAPI = new YoutubeAPI();

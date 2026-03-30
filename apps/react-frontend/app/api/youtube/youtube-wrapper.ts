import axios from "axios";

import { stringify } from "../../utils/misc";

import type {
  YoutubePlaylist,
  YoutubePlaylistItem,
  YoutubeVideo,
  YoutubeSearch,
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


class YoutubeSearchAPI {

  private baseURL: string;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  async search(queryParams : {q : string, max_results? : number}): Promise<YoutubeSearch> {
    // Get a list of searches for search string
    try {
      const q = stringify(queryParams);
      const response = await axios.get<YoutubeSearch>(`${this.baseURL}?${q}`);
      const results: YoutubeVideo[] = (response.data.results || []).map((item: any) => ({
        youtube_id: item.youtube_id,
        title: item.title,
        creator: item.creator,
        thumbnail: item.thumbnail,
        duration: item.duration,

        source_url: '',
        created_at: '',
        tags: [],
      }));

      return {
        query: response.data.query,
        results,
      };
    } catch (error) {
      throw new Error(`Failed to search: ${queryParams.q}`);
    }
  }

}


class YoutubeAPI {
  public video: YoutubeVideoAPI;
  public search: YoutubeSearchAPI;

  constructor() {
    const baseURL = `${import.meta.env.VITE_API_URL}/youtube`;
    this.video = new YoutubeVideoAPI(`${baseURL}/videos`);
    this.search = new YoutubeSearchAPI(`${baseURL}/search`);
  }
}

export const youtubeAPI = new YoutubeAPI();

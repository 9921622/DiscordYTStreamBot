import axios from "axios";
import type { DiscordUser } from "./backend-types"


class DiscordAPI {
  private baseURL: string;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  oauth2URI() {
    return `${this.baseURL}/oauth`;
  }

  async get_user() {
    try {
        const response = await axios.get<DiscordUser>(`${this.baseURL}/profile`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('access')}` }
      });
      return response.data;
    } catch (error) {
        throw new Error("Failed to get profile check access tokens");
    }
  }

  async get_voice_channel_id() {
    try {
        const response = await axios.get<DiscordUser>(`${this.baseURL}/get-voice-channel`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('access')}` }
      });
      return response.data;
    } catch (error) {
        throw new Error("Failed to get voice channel check access tokens");
    }
  }

}

class DiscordGuildQueueAPI {
  private baseURL: string

  constructor(baseURL: string) {
    this.baseURL = baseURL
  }

  private get headers() {
    return { Authorization: `Bearer ${localStorage.getItem('access')}` }
  }

  async get(guild_id: string) {
    const response = await axios.get(`${this.baseURL}/guild/${guild_id}/queue/`, { headers: this.headers })
    return response.data
  }

  async clear(guild_id: string) {
    const response = await axios.delete(`${this.baseURL}/guild/${guild_id}/queue/`, { headers: this.headers })
    return response.data
  }

  async addItem(guild_id: string, youtube_id: string) {
    const response = await axios.post(`${this.baseURL}/guild/${guild_id}/queue/items/`, { youtube_id }, { headers: this.headers })
    return response.data
  }

  async removeItem(guild_id: string, item_id: number) {
    const response = await axios.delete(`${this.baseURL}/guild/${guild_id}/queue/items/${item_id}/`, { headers: this.headers })
    return response.data
  }

  async reorder(guild_id: string, order: number[]) {
    const response = await axios.patch(`${this.baseURL}/guild/${guild_id}/queue/items/`, { order }, { headers: this.headers })
    return response.data
  }
}

class BackendAPI {
  public discord: DiscordAPI
  public queue: DiscordGuildQueueAPI

  constructor() {
    const baseURL = `${import.meta.env.VITE_API_URL}`
    this.discord = new DiscordAPI(`${baseURL}/discord`)
    this.queue = new DiscordGuildQueueAPI(`${baseURL}/discord`)
  }

  refresh_token_uri() {
    return `${import.meta.env.VITE_API_URL}/token/refresh/`
  }
}

export const backendAPI = new BackendAPI();

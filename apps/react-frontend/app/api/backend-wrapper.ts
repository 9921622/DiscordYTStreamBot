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

class BackendAPI {
  public discord : DiscordAPI;

  constructor() {
    const baseURL = `${import.meta.env.VITE_API_URL}`;
    this.discord = new DiscordAPI(`${baseURL}/discord`);
  }

  refresh_token_uri() {
    return `${import.meta.env.VITE_API_URL}/token/refresh/`
  }
}

export const backendAPI = new BackendAPI();

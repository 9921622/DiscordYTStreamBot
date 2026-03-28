import axios from "axios";

import type { PlaybackStatus } from "./discord-types";
import { stringify } from "../../utils/misc";


class MusicControlAPI {
  private baseURL: string;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  async play(guild_id: string, video_id: string, offset: number = 0.0): Promise<{ ok: boolean }> {
    const response = await axios.get(`${this.baseURL}/play`, {
      params: { guild_id, video_id, offset },
    });
    return response.data;
  }

  async pause(guild_id: string): Promise<{ ok: boolean; paused: boolean }> {
    const response = await axios.get(`${this.baseURL}/pause`, {
      params: { guild_id },
    });
    return response.data;
  }

  async stop(guild_id: string): Promise<{ ok: boolean }> {
    const response = await axios.get(`${this.baseURL}/stop`, {
      params: { guild_id },
    });
    return response.data;
  }

  async seek(guild_id: string, time: number): Promise<{ ok: boolean; position: number }> {
    const response = await axios.get(`${this.baseURL}/seek`, {
      params: { guild_id, time },
    });
    return response.data;
  }

  async status(guild_id: string): Promise<PlaybackStatus> {
    const response = await axios.get<PlaybackStatus>(`${this.baseURL}/status`, {
      params: { guild_id },
    });
    return response.data;
  }

  async getVolume(guild_id: string): Promise<{ ok: boolean; volume: number }> {
    const response = await axios.get(`${this.baseURL}/volume`, {
      params: { guild_id },
    });
    return response.data;
  }

  async setVolume(guild_id: string, level: number): Promise<{ ok: boolean; volume: number }> {
    const response = await axios.get(`${this.baseURL}/volume`, {
      params: { guild_id, level },
    });
    return response.data;
  }
}


class DiscordBotAPI {
  public musicControl: MusicControlAPI;

  constructor() {
    const baseURL = `${import.meta.env.VITE_DISCORD_BOT_URL}`;

    this.musicControl = new MusicControlAPI(`${baseURL}/music-control`);
  }
}

export const discordBotAPI = new DiscordBotAPI();

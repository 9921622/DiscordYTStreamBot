import axios from "axios";

class VoiceAPI {
  private baseURL: string;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  async get_user_vc(user_id: string): Promise<{
        channel_id: string | null,
        channel_name?: string,
        guild_id?: string,
        guild_name?: string,
        bot_in_channel?: boolean,
      }> {
    const response = await axios.get(`${this.baseURL}/user-voice-channel`, {
        params: { user_id }
    })
    return response.data
  }

  async join_user_vc(user_id: string): Promise<{ ok: boolean, error?: string }> {
    const response = await axios.get(`${this.baseURL}/join-user`, {
        params: { user_id }
    })
    return response.data
  }

  async disconnect_vc(guild_id: string): Promise<{ ok: boolean }> {
    const response = await axios.get(`${this.baseURL}/disconnect`, {
      params: { guild_id }
    })
    return response.data
  }
}

class DiscordBotAPI {
  public voice: VoiceAPI;

  constructor() {
    const baseURL = `${import.meta.env.VITE_DISCORD_BOT_URL}`;
    this.voice = new VoiceAPI(`${baseURL}/voice`);
  }
}

export const discordBotAPI = new DiscordBotAPI();

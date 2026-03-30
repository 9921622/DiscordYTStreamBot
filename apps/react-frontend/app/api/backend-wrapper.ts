import axios from "axios";

class DiscordAPI {
  private baseURL: string;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  oauth2URI() {
    return `${this.baseURL}/oauth`;
  }
}

class BackendAPI {
  public discord : DiscordAPI;

  constructor() {
    const baseURL = `${import.meta.env.VITE_API_URL}`;
    this.discord = new DiscordAPI(`${baseURL}/discord`);
  }
}

export const backendAPI = new BackendAPI();

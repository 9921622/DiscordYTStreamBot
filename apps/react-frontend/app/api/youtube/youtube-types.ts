export interface YoutubeVideo {
  youtube_id: string;
  title: string;
  creator: string;
  source_url: string;
  duration: number;
  thumbnail?: string;
  created_at: string;
  tags: YoutubeTag[];
}

export interface YoutubeTag {
  id: number;
  name: string;
}

export interface YoutubePlaylist {
  id: number;
  name: string;
  playlist_type: string;
  user: number;
  created_at: string;
  updated_at: string;
  youtube_playlist_id?: string;
}

export interface YoutubePlaylistItem {
  id: number;
  playlist: number;
  video: string;
  order: number;
}


export interface YoutubeSearch {
  query : string;
  results? : YoutubeSearchItem[];
}

export interface YoutubeSearchItem {
  id : string;
  title : string;
  creator : string;
  thumbnail : string;
  duration : number;
}

import { PlayIcon } from "./utilities/Icons";
import { NumToTime } from "./utilities/misc";

import type { YoutubeVideo } from "~/api/youtube/youtube-types";


export default function SongSearchbarCard({ song, onClick }: { song: YoutubeVideo, onClick?: () => void; }) {
  return (
    <div
      className="flex items-center gap-3 px-2 py-1.5 rounded-lg hover:bg-zinc-800/70 active:bg-zinc-700/50 transition-colors cursor-pointer group"
      onClick={onClick}
    >
      {/* Thumbnail */}
      <div className="relative w-16 h-16 flex-shrink-0 rounded-md overflow-hidden">
        <img
          src={song.thumbnail}
          alt={song.title}
          className="w-full h-full object-cover transition-transform duration-200 group-hover:scale-105"
        />

        {/* Play overlay */}
        <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity duration-150 flex items-center justify-center">
          <div className="w-6 h-6 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center">
            <PlayIcon />
          </div>
        </div>

        {/* Duration badge */}
        <div className="absolute bottom-0.5 right-0.5 bg-black/75 text-[9px] font-medium px-1 py-px rounded text-white/90 leading-tight">
          {NumToTime(song.duration)}
        </div>
      </div>

      {/* Text */}
      <div className="flex flex-col justify-center flex-1 min-w-0 gap-0.5">
        <p className="text-[13px] font-medium text-zinc-100 truncate leading-snug">
          {song.title}
        </p>
        <p className="text-[11px] text-zinc-500 truncate leading-snug group-hover:text-zinc-400 transition-colors">
          {song.creator}
        </p>
      </div>
    </div>
  );
}

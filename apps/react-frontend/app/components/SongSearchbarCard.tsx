import { PlayIcon } from "./utilities/Icons";
import { NumToTime } from "./utilities/misc";

import type { YoutubeVideo } from "~/api/youtube/youtube-types";


export default function SongSearchbarCard({ song, onClick }: { song: YoutubeVideo, onClick?: () => void; }) {
  return (
    <div className="flex items-center gap-3 p-2 rounded-md hover:bg-zinc-800 transition cursor-pointer group"
         onClick={onClick}>

      <div className="relative w-14 h-14 flex-shrink-0">

        <img
          src={song.thumbnail}
          alt={song.title}
          className="w-full h-full object-cover rounded-md"
        />
        <div className="absolute inset-0 bg-black/50 rounded-md opacity-0 group-hover:opacity-100 transition flex items-center justify-center">
          <PlayIcon />
        </div>

        <div className="absolute bottom-1 right-1 bg-black/80 text-[10px] px-1 rounded text-white">
          {NumToTime(song.duration)}
        </div>
      </div>

      <div className="flex flex-col justify-center flex-1 overflow-hidden">
        <p className="text-sm font-semibold text-white truncate">
          {song.title}
        </p>
        <p className="text-xs text-gray-400 truncate">
          {song.creator}
        </p>
      </div>

    </div>
  );
}

import { useBotContext } from "~/contexts/BotContext"
import { usePlaylistContext } from "~/contexts/PlaylistContext"
import { usePlaybackStatusContext } from "~/contexts/PlaybackStatusContext"
import { useCurrentPlayback } from "~/hooks/useCurrentPlayback"
import type { YoutubeVideo } from "~/api/youtube/youtube-types"
import { Plus } from "lucide-react"
import { PlayPauseIcon } from "./utilities/Icons"

export default function SongCard({ song }: { song: YoutubeVideo }) {
    const { botInChannel } = useBotContext()
    const { add, playNow } = usePlaylistContext()
    const { videoPause } = usePlaybackStatusContext()
    const { isPlaying, isPaused, currentItem } = useCurrentPlayback()

    const isCurrentSong = currentItem?.video?.youtube_id === song.youtube_id
    const isThisSongPlaying = isCurrentSong && isPlaying && !isPaused
    const isThisSongPaused  = isCurrentSong && isPaused

    function handlePlay() {
        if (isCurrentSong) {
            videoPause()
        } else {
            playNow(song)
        }
    }

    return (
        <div
            className={[
                "relative w-full aspect-square rounded-xl overflow-hidden group bg-zinc-900",
                isCurrentSong ? "ring-2 ring-primary ring-offset-2 ring-offset-base-100" : "",
                !botInChannel ? "cursor-not-allowed" : "cursor-pointer",
            ].join(" ")}
        >
            <img
                src={song.thumbnail || ""}
                alt={song.title}
                className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
            />

            <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/30 to-transparent" />

            <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                <button
                    className="btn btn-ghost btn-circle btn-xs bg-black/50 hover:bg-black/70 text-white"
                    onClick={() => add(song)}
                    disabled={!botInChannel}
                    title="Add to queue"
                >
                    <Plus className="w-3.5 h-3.5" />
                </button>
            </div>

            <div className="absolute bottom-0 left-0 right-0 p-2.5 flex items-end justify-between gap-2">
                <div className="min-w-0 flex-1">
                    <h2 className="text-white text-xs font-semibold line-clamp-2 leading-snug">
                        {song.title}
                    </h2>
                    <p className="text-white/50 text-[11px] truncate mt-0.5">
                        {song.creator}
                    </p>
                </div>

                <button
                    className={[
                        "btn btn-circle btn-lg flex-shrink-0 transition-transform duration-200 transform hover:scale-105",
                        "opacity-0 group-hover:opacity-100 translate-y-1 group-hover:translate-y-0",
                        isThisSongPlaying ? "btn-secondary" : "btn-primary",
                    ].join(" ")}
                    onClick={handlePlay}
                    disabled={!botInChannel}
                    title={isThisSongPlaying ? "Pause" : isThisSongPaused ? "Resume" : "Play"}
                >
                    <div className="transform transition-transform duration-200 scale-100">
                        <PlayPauseIcon
                            className="w-5 h-5 flex-shrink-0 text-white"
                            isPlaying={isThisSongPlaying}
                        />
                    </div>
                </button>
            </div>
        </div>
    )
}

import { PlayIcon, PauseIcon, CrossIcon } from "./utilities/Icons";
import { useBotContext } from "~/contexts/BotContext";
import { usePlaybackVideoContext } from "~/contexts/PlaybackVideoContext";
import { usePlaybackQueueContext } from "~/contexts/PlaybackQueueContext";
import type { YoutubeVideo } from "~/api/youtube/youtube-types";

export default function SongCard({ song }: { song: YoutubeVideo }) {
    const { botInChannel } = useBotContext()
    const { videoPlay, videoPause, video: currentVideo, videoPlaybackStatus } = usePlaybackVideoContext()
    const { queueAdd } = usePlaybackQueueContext()

    const isCurrentSong = currentVideo?.youtube_id === song.youtube_id
    const isPlaying = isCurrentSong && videoPlaybackStatus?.playing && !videoPlaybackStatus?.paused
    const isPaused = isCurrentSong && videoPlaybackStatus?.paused

    function handlePlay() {
        if (isPlaying) {
            videoPause()         // pause if currently playing
        } else if (isPaused) {
            videoPause()         // unpause if currently paused
        } else {
            videoPlay(song)      // play fresh
        }
    }

    return (
        <div className={`relative w-48 h-48 rounded-lg overflow-hidden group bg-zinc-900 ${!botInChannel ? "cursor-not-allowed" : ""}`}>
            <img
                src={song.thumbnail || ""}
                alt={song.title}
                className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"/>

            <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent flex flex-col p-3">

                <div className="absolute bottom-3 right-3 opacity-0 group-hover:opacity-100 transition-all translate-y-2 group-hover:translate-y-0">
                    <div className="flex gap-2">
                        <button
                            className="btn btn-secondary btn-circle btn-sm"
                            onClick={() => queueAdd(song, !!videoPlaybackStatus?.playing)}
                            disabled={!botInChannel}
                        >
                            <CrossIcon />
                        </button>

                        <button
                            className="btn btn-primary btn-circle btn-sm"
                            onClick={handlePlay}
                            disabled={!botInChannel}
                        >
                            {isPlaying ? <PauseIcon /> : <PlayIcon />}
                        </button>
                    </div>
                </div>

                {/* Push text to bottom */}
                <div className="mt-auto">
                    <h2 className="text-white text-sm font-semibold line-clamp-2">
                        {song.title}
                    </h2>
                    <p className="text-gray-400 text-xs truncate">
                        {song.creator}
                    </p>
                </div>
            </div>
        </div>
    );
}

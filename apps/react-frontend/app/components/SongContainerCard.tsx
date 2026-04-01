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
        <div className={`card bg-base-100 w-50 h-50 shadow-sm relative overflow-hidden group ${!botInChannel ? "cursor-not-allowed" : ""}`}>
            <figure className="h-full">
                <img src={song.thumbnail || ""} alt={song.title} className="w-full h-full object-cover" />
            </figure>

            <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black via-black/70 to-transparent p-4">
                <h2 className="card-title text-white text-lg line-clamp-2">{song.title}</h2>
                <p className="text-gray-300 text-sm">{song.creator}</p>

                <div className="card-actions justify-between mt-3 opacity-0 group-hover:opacity-100 transition-opacity">
                    <div className="tooltip tooltip-top" data-tip={!botInChannel ? "Bot is not in your voice channel" : "Add to queue"}>
                        <button
                            className="btn btn-ghost btn-circle btn-sm text-white"
                            onClick={() => queueAdd(song, !!videoPlaybackStatus?.playing)}
                            disabled={!botInChannel}
                        >
                            <CrossIcon />
                        </button>
                    </div>
                    <div className="tooltip tooltip-top"
                            data-tip={!botInChannel ? "Bot is not in your voice channel" : isPlaying ? "Pause" : "Play"}>
                        <button
                            className="btn btn-primary btn-circle btn-sm"
                            onClick={handlePlay}
                            disabled={!botInChannel}
                        >
                            {isPlaying ? <PauseIcon /> : <PlayIcon />}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    )
}

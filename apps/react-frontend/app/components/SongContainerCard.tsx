// SongCard.tsx
import { PlayIcon, PauseIcon, CrossIcon } from "./utilities/Icons";
import { useBotContext } from "~/contexts/BotContext";
import { usePlaybackVideoContext } from "~/contexts/PlaybackVideoContext";
import { usePlaybackQueueContext } from "~/contexts/PlaybackQueueContext";
import type { YoutubeVideo } from "~/api/youtube/youtube-types";

export default function SongCard({ song }: { song: YoutubeVideo }) {
    const { botInChannel } = useBotContext();
    const { videoPlay, videoPause, video: currentVideo, videoPlaybackStatus } = usePlaybackVideoContext();
    const { queueAdd } = usePlaybackQueueContext();

    const isCurrentSong = currentVideo?.youtube_id === song.youtube_id;
    const isPlaying = isCurrentSong && videoPlaybackStatus?.playing && !videoPlaybackStatus?.paused;
    const isPaused = isCurrentSong && videoPlaybackStatus?.paused;

    function handlePlay() {
        if (isPlaying) {
            videoPause();
        } else if (isPaused) {
            videoPause();
        } else {
            videoPlay(song);
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

            {/* Gradient overlay — always visible at bottom, stronger on hover */}
            <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/30 to-transparent" />

            {/* Top-right: queue button — appears on hover */}
            <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                <button
                    className="btn btn-ghost btn-circle btn-xs bg-black/50 hover:bg-black/70 text-white"
                    onClick={() => queueAdd(song, !!videoPlaybackStatus?.playing)}
                    disabled={!botInChannel}
                    title="Add to queue"
                >
                    <CrossIcon />
                </button>
            </div>

            {/* Bottom: title + play button */}
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
                        "btn btn-circle btn-sm flex-shrink-0 transition-all duration-200",
                        "opacity-0 group-hover:opacity-100 translate-y-1 group-hover:translate-y-0",
                        isPlaying ? "btn-secondary" : "btn-primary",
                    ].join(" ")}
                    onClick={handlePlay}
                    disabled={!botInChannel}
                    title={isPlaying ? "Pause" : isPaused ? "Resume" : "Play"}
                >
                    {isPlaying ? <PauseIcon /> : <PlayIcon />}
                </button>
            </div>
        </div>
    );
}

import { useEffect, useState } from "react";
import { useBotContext } from "~/contexts/BotContext"
import { useSocketContext } from "~/contexts/SocketContext"
import { usePlaybackVideoContext } from "~/contexts/PlaybackVideoContext";
import { usePlaybackQueueContext } from "~/contexts/PlaybackQueueContext";

import ArtistInfo from "./MusicbarArtistInfo";
import SongProgressBar from "./MusicbarSongProgressBar";
import SongControls from "./MusicbarSongControls";
import MusicbarTags from "./MusicbarTags";
import VolumeControl from "./MusicbarVolumeControl";


export default function Musicbar() {
    const { send } = useSocketContext();
    const { video, videoLoading, videoError, videoPlaybackStatus, videoPause, videoVolume } = usePlaybackVideoContext()
    const { queueNext } = usePlaybackQueueContext()
    const { guildID, botInChannel } = useBotContext()

    const isPlaying = videoPlaybackStatus?.playing ?? false;
    const isPaused  = videoPlaybackStatus?.paused ?? false;
    const isLoop    = videoPlaybackStatus?.loop   ?? false;
    const volume    = videoPlaybackStatus?.volume ?? 0.5;

    const [currentTime, setCurrentTime] = useState(videoPlaybackStatus?.position ?? 0)

    // keep currentTime in sync when status arrives (seek, play, etc.)
    useEffect(() => {
        if (videoPlaybackStatus?.position !== undefined) {
            setCurrentTime(videoPlaybackStatus.position)
        }
    }, [videoPlaybackStatus?.position])

    // local tick between server pushes
    useEffect(() => {
        if (!isPlaying || isPaused) return
        const timer = setInterval(() => setCurrentTime(t => t + 1), 1000)
        return () => clearInterval(timer)
    }, [isPlaying, isPaused])

    // ---- handlers ----

    const handlePause = () => {
        if (!guildID) return
        videoPause()
    }

    const handleLoop = () => {
        if (!guildID) return
        send({ type: "loop" })
    }

    const handleSeek = (time: number) => {
        if (!guildID) return
        setCurrentTime(time)
        send({ type: "seek", position: time })
    }

    const handleVolume = (level: number) => {
        if (!guildID) return
        videoVolume(level)
    }

    // ---- render ----

    if (videoError) return (
        <div className="bg-gray-900 text-white px-4 py-5 fixed bottom-0 w-full flex items-center justify-center">
            <div className="alert alert-error w-auto">
                <span>⚠️ {videoError}</span>
            </div>
        </div>
    )

    const disabled = !video || !botInChannel

    return (
        <div className="bg-gray-900 text-white px-4 py-5 flex items-center justify-between shadow-inner fixed bottom-0 w-full">
            {video?.thumbnail && (
                <>
                    <style>{`
                        @keyframes bgDrift {
                            0%   { transform: scale(1.1) translate(0%, 0%)    skew(0deg, 0deg); }
                            25%  { transform: scale(1.2) translate(-2%, 1%)   skew(1deg, 0.5deg); }
                            50%  { transform: scale(1.15) translate(2%, -1%)  skew(-1deg, 1deg); }
                            75%  { transform: scale(1.2) translate(-1%, 2%)   skew(0.5deg, -1deg); }
                            100% { transform: scale(1.1) translate(0%, 0%)    skew(0deg, 0deg); }
                        }
                    `}</style>
                    <div
                        className="absolute inset-0 transition-all duration-1000"
                        style={{
                            backgroundImage: `url(${video?.thumbnail})`,
                            backgroundSize: 'cover',
                            backgroundPosition: 'center',
                            filter: 'blur(20px) brightness(0.4)',
                            animation: 'bgDrift 12s ease-in-out infinite',
                        }}
                    />
                    <div className="absolute inset-0 bg-black/50" />
                </>
            )}
            {!video?.thumbnail && <div className="absolute inset-0 bg-gray-900" />}

            <div className="relative z-10 flex items-center gap-3 w-1/4 min-w-0">
                <ArtistInfo video={video} loading={videoLoading} />
            </div>

            <div className={`absolute left-1/2 -translate-x-1/2 ${disabled ? "cursor-not-allowed" : ""}`}>
                <div className={`flex flex-col items-center gap-2 w-150 ${disabled ? "opacity-40 pointer-events-none" : ""}`}>
                    {!botInChannel && video && (
                        <p className="text-xs text-warning">Bot is not in your voice channel</p>
                    )}
                    <SongControls
                        className="w-1/2"
                        isPlaying={isPlaying}
                        isPaused={isPaused}
                        isLoop={isLoop}
                        onPause={handlePause}
                        onNext={queueNext}
                        onLoop={handleLoop}
                    />
                    <SongProgressBar
                        className="w-full"
                        currentTime={currentTime}
                        setCurrentTime={handleSeek}
                        duration={video?.duration ?? 0}
                    />
                </div>
            </div>

            <div className="relative z-10 flex items-center gap-2 w-1/6 justify-end ml-auto">
                <MusicbarTags tags={video?.tags ?? []} />
            </div>

            <div className="relative z-10 flex items-center gap-3">
                <VolumeControl volume={volume} onVolumeChange={handleVolume} />
            </div>
        </div>
    );
}

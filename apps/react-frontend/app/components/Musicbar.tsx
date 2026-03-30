import { useSearchParams } from "react-router";
import { useEffect, useState } from "react";
import type { YoutubeVideo } from "~/api/youtube/youtube-types";
import { discordBotAPI } from "~/api/discord/discord-wrapper";
import { useBotContext } from "~/contexts/BotContext"

import ArtistInfo from "./MusicbarArtistInfo";
import SongProgressBar from "./MusicbarSongProgressBar";
import SongControls from "./MusicbarSongControls";
import MusicbarTags from "./MusicbarTags";
import VolumeControl from "./MusicbarVolumeControl";


function usePlaybackStatus(guildID: string | null, video: YoutubeVideo | null) {
    const [currentTime, setCurrentTime] = useState(0)
    const [isPlaying, setIsPlaying] = useState(false)
    const [isPaused, setIsPaused] = useState(false)
    const [volume, setVolume] = useState(1.0)

    const poll = async () => {
        if (!guildID) return
        try {
            const status = await discordBotAPI.musicControl.status(guildID)
            setCurrentTime(status.position)
            setIsPlaying(status.playing)
            setIsPaused(status.paused)
            setVolume(status.volume)
        } catch {}
    }

    // local tick
    useEffect(() => {
        if (!isPlaying || isPaused) return
        const timer = setInterval(() => setCurrentTime(t => t + 1), 1000)
        return () => clearInterval(timer)
    }, [isPlaying, isPaused])

    // poll on video change
    useEffect(() => {
        if (!video) return
        poll()
        const interval = setInterval(poll, 5000)
        return () => clearInterval(interval)
    }, [video])

    return { currentTime, setCurrentTime, isPlaying, isPaused, setIsPaused, volume, setVolume, poll }
}


export default function Musicbar({ video, loading, error }: { video: YoutubeVideo | null; loading: boolean; error: string | null }) {
    const [searchParams, setSearchParams] = useSearchParams()
    const { guildID, botInChannel } = useBotContext()

    const { currentTime, setCurrentTime, isPlaying, isPaused, setIsPaused, volume, setVolume, poll } = usePlaybackStatus(guildID, video)

    // poll on searchParams change
    useEffect(() => { poll() }, [searchParams])

    const handlePause = async () => {
        if (!guildID) return
        await discordBotAPI.musicControl.pause(guildID)
        setIsPaused(p => !p)
        await poll()
    }

    const handleSeek = async (time: number) => {
        if (!guildID) return
        setCurrentTime(time)
        await discordBotAPI.musicControl.seek(guildID, time)
        await poll()
    }

    const handleVolume = async (level: number) => {
        if (!guildID) return
        await discordBotAPI.musicControl.setVolume(guildID, level)
        setVolume(level)
        setSearchParams(prev => { prev.set("vol", String(level)); return prev }, { replace: true })
    }

    if (error) return (
        <div className="bg-gray-900 text-white px-4 py-5 fixed bottom-0 w-full flex items-center justify-center">
            <div className="alert alert-error w-auto">
                <span>⚠️ {error}</span>
            </div>
        </div>
    )

    const disabled = !video || !botInChannel

    return (
        <div className="bg-gray-900 text-white px-4 py-5 flex items-center justify-between shadow-inner fixed bottom-0 w-full">

            <div className="flex items-center gap-3 w-1/4 min-w-0">
                <ArtistInfo video={video} loading={loading} />
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
                        onPause={handlePause}
                    />
                    <SongProgressBar
                        className="w-full"
                        currentTime={currentTime}
                        setCurrentTime={handleSeek}
                        duration={video?.duration ?? 0}
                    />
                </div>
            </div>

            <div className="flex items-center gap-2 w-1/6 justify-end ml-auto">
                <MusicbarTags tags={video?.tags ?? []} />
            </div>

            <div className="flex items-center gap-3">
                <VolumeControl volume={volume} onVolumeChange={handleVolume} />
            </div>

        </div>
    )
}

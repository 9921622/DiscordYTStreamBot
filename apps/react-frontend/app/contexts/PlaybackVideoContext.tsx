import { createContext, useContext, useEffect, useState } from "react"
import type { ReactNode } from "react"
import type { YoutubeVideo } from "~/api/youtube/youtube-types"
import type { PlaybackStatus } from "~/api/discord/discord-types"
import { useBotContext } from "./BotContext"
import { youtubeAPI } from "~/api/youtube/youtube-wrapper"
import { useSocketContext } from "./SocketContext"
import { backendAPI } from "~/api/backend-wrapper"



interface PlaybackVideoContextType {
    video: YoutubeVideo | null
    videoLoading: boolean
    videoError: string | null
    videoPlay: (item: YoutubeVideo) => void
    videoStop: () => void
    videoPause: () => void
    videoVolume: (level: number) => void
    videoPlaybackStatus: PlaybackStatus | null
}

const PlaybackVideoContext = createContext<PlaybackVideoContextType>({
    video: null,
    videoLoading: false,
    videoError: null,
    videoPlay: () => {},
    videoStop: () => {},
    videoPause: () => {},
    videoVolume: () => {},
    videoPlaybackStatus: null,
})

export function PlaybackVideoProvider({ children }: { children: ReactNode }) {
    const { send, on, connected } = useSocketContext();
    const { guildID, botInChannel } = useBotContext();
    const [video, setVideo] = useState<YoutubeVideo | null>(null);
    const [videoLoading, setVideoLoading] = useState<boolean>(false);
    const [videoError, setVideoError] = useState<string | null>(null);
    const [videoPlaybackStatus, setVideoPlaybackStatus] = useState<PlaybackStatus | null>(null);

    useEffect(() => {
        if (!guildID || !botInChannel || !connected) return
        send({ type: "status" })
    }, [guildID, botInChannel, connected])

    // websocket hooks
    // ==============================================================================================================

    useEffect(() => on("status", async (data) => {
        /* catches the status response
            {"type": "status", "playback": bot.vc_get_status(guild_id)}
        */
        const status = data.playback as PlaybackStatus
        setVideoPlaybackStatus(status)
        if (!status.playing || !status.video_id) return
        try {
            const fetched = await youtubeAPI.video.retrieve(status.video_id)
            setVideo(fetched)
        } catch {
            setVideo(null)
        }
    }), [on])

    useEffect(() => on("play", (data) => {
        if (data.error) {
            setVideoError(data.error as string);
            setVideo(null);
            setVideoLoading(false);
            return;
        }

        // get youtube video from Id
        youtubeAPI.video.retrieve(data.video_id as string)
            .then(video => {
                setVideo(video)
                setVideoLoading(false)
                console.log("test");
            })
            .catch(() => {
                setVideoError("Failed to fetch video info")
                setVideoLoading(false)
            })
    }), [on])

    useEffect(() => on("pause", (data) => {
        if (data.error) return
        setVideoPlaybackStatus(prev => prev ? { ...prev, paused: data.paused as boolean } : prev)
    }), [on])

    useEffect(() => on("volume", (data) => {
        if (data.error) return
        setVideoPlaybackStatus(prev => prev ? { ...prev, volume: data.volume as number } : prev)
    }), [on])

    useEffect(() => on("song_start", async (data) => {
        setVideoError(null)
        try {
            const fetched = await youtubeAPI.video.retrieve(data.video_id as string)
            setVideo(fetched)
        } catch {
            setVideo(null)
        } finally {
            setVideoLoading(false)
        }
    }), [on])

    useEffect(() => on("song_end", () => {
        setVideo(null)
        setVideoPlaybackStatus(null)
    }), [on])

    useEffect(() => on("*", (data) => {
        console.log(data);
    }), [on])


    // ==============================================================================================================


    function videoPlay(item: YoutubeVideo) {
        if (!botInChannel) return
        setVideoError(null)
        setVideoLoading(true)
        send({ type: "play", video_id: item.youtube_id, offset: 0, volume: videoPlaybackStatus?.volume || 0.5 })

        // optimistically set video so UI responds immediately
        setVideo(item)
    }

    function videoStop() {
        send({ type: "stop" })
        setVideo(null)
        setVideoPlaybackStatus(null)
        setVideoLoading(false)
    }

    function videoPause() {
        send({ type: "pause" })
    }

    function videoVolume(level: number) {
        send({ type: "volume", level })
        // optimistically update so the slider feels instant
        setVideoPlaybackStatus(prev => prev ? { ...prev, volume: level } : prev)
    }


    return (
        <PlaybackVideoContext.Provider value={{
                    video, videoLoading, videoError, videoPlay, videoStop,
                    videoPause, videoVolume,
                    videoPlaybackStatus,
                }}>
            {children}
        </PlaybackVideoContext.Provider>
    )
}
export const usePlaybackVideoContext = () => useContext(PlaybackVideoContext)

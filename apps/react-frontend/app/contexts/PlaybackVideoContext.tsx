import { createContext, useContext, useEffect, useState } from "react"
import type { ReactNode } from "react"
import type { YoutubeVideo } from "~/api/youtube/youtube-types"
import type { PlaybackStatus } from "~/api/discord/discord-types"
import { useBotContext } from "./BotContext"
import { youtubeAPI } from "~/api/youtube/youtube-wrapper"
import { useSocketContext } from "./SocketContext"
import type { WSResponse } from "~/api/backend-types"


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

    useEffect(() => on("status", async (resp: WSResponse) => {
        if (!resp.success || !resp.data) return;

        const status = resp.data.playback as PlaybackStatus;
        setVideoPlaybackStatus(status);

        if (!status.playing || !status.video_id) return;

        try {
            const fetched = await youtubeAPI.video.retrieve(status.video_id);
            setVideo(fetched);
        } catch {
            setVideo(null);
        }
    }), [on]);

    useEffect(() => on("play", async (resp: WSResponse) => {
        if (!resp.success || !resp.data) {
            setVideoError(resp.error?.message || "Unknown error");
            setVideo(null);
            setVideoLoading(false);
            return;
        }

        try {
            const video = await youtubeAPI.video.retrieve(resp.data.video_id as string);
            setVideo(video);
            setVideoLoading(false);
        } catch {
            setVideoError("Failed to fetch video info");
            setVideoLoading(false);
        }
    }), [on]);

    useEffect(() => on("stop", (resp: WSResponse) => {
        if (!resp.success) return;
        setVideo(null);
        setVideoPlaybackStatus(null);
        setVideoLoading(false);
    }), [on]);

    useEffect(() => on("pause", (resp: WSResponse) => {
        if (!resp.success || !resp.data) return
        const { paused } = resp.data
        if (typeof paused !== "boolean") return
        setVideoPlaybackStatus(prev => prev ? { ...prev, paused } : prev)
    }), [on])

    useEffect(() => on("volume", (resp: WSResponse) => {
        if (!resp.success || !resp.data) return
        const { volume } = resp.data
        if (typeof volume !== "number") return
        setVideoPlaybackStatus(prev => prev ? { ...prev, volume } : prev)
    }), [on])

    useEffect(() => on("loop", (resp: WSResponse) => {
        if (!resp.success || !resp.data) return
        const { loop } = resp.data
        if (typeof loop !== "boolean") return
        setVideoPlaybackStatus(prev => prev ? { ...prev, loop } : prev)
    }), [on])

    useEffect(() => on("song_end", (resp: WSResponse) => {
        if (!resp.success || !resp.data) return;
        if (resp.data.next_song) setVideoLoading(true);
        setVideo(null);
        setVideoPlaybackStatus(null);
    }), [on]);

    useEffect(() => on("*", (resp: WSResponse) => {
        console.log(resp);
    }), [on]);

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

import { createContext, useContext, useEffect, useState, type ReactNode } from "react"
import { useSearchParams } from "react-router"
import { youtubeAPI } from "~/api/youtube/youtube-wrapper"
import { discordBotAPI } from "~/api/discord/discord-wrapper"
import { useBotContext } from "~/contexts/BotContext"
import type { YoutubeVideo } from "~/api/youtube/youtube-types"

interface PlaybackContextType {
    video: YoutubeVideo | null
    videoLoading: boolean
    playError: string | null
    SongOnClick: (item: YoutubeVideo) => void
}

const PlaybackContext = createContext<PlaybackContextType>({
    video: null,
    videoLoading: false,
    playError: null,
    SongOnClick: () => {},
})

export function PlaybackProvider({ children }: { children: ReactNode }) {
    const [searchParams, setSearchParams] = useSearchParams()
    const { guildID, botInChannel } = useBotContext()

    const videoId = searchParams.get("v");
    const volume = Number(searchParams.get("vol") ?? 0.5);

    const [video, setVideo] = useState<YoutubeVideo | null>(null);
    const [videoLoading, setVideoLoading] = useState(false);
    const [playError, setPlayError] = useState<string | null>(null);

    // get video
    useEffect(() => {
        if (!guildID || !videoId || !botInChannel) return

        setPlayError(null)
        setVideo(null)
        setVideoLoading(true)

        discordBotAPI.musicControl.play(guildID, videoId, 0, volume).catch((err: any) => {
            const message = err?.response?.data?.detail?.error
                || (typeof err?.response?.data?.detail === 'string' ? err?.response?.data?.detail : null)
                || "Failed to play track"
            setPlayError(message)
            setVideo(null)
            setVideoLoading(false)
        })

        youtubeAPI.video.retrieve(videoId).then(setVideo).catch(() => setVideo(null)).finally(() => setVideoLoading(false))
    }, [videoId, guildID, botInChannel])

    // if no video use status to see if currently playing an update video
    useEffect(() => {
        if (!guildID || !botInChannel || videoId) return

        discordBotAPI.musicControl.status(guildID).then(async status => {
            if (!status.playing || !status.video_id) return
            const fetchedVideo = await youtubeAPI.video.retrieve(status.video_id)
            setVideo(fetchedVideo)
        }).catch(() => {})
    }, [guildID, botInChannel])

    function SongOnClick(item: YoutubeVideo) {
        setSearchParams(prev => { prev.set("v", item.youtube_id); return prev })
    }

    return (
        <PlaybackContext.Provider value={{ video, videoLoading, playError, SongOnClick }}>
            {children}
        </PlaybackContext.Provider>
    )
}

export const usePlayback = () => useContext(PlaybackContext)

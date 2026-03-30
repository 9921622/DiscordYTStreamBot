import { createContext, useContext, useEffect, useState, type ReactNode } from "react"
import { useSearchParams } from "react-router"
import { youtubeAPI } from "~/api/youtube/youtube-wrapper"
import { discordBotAPI } from "~/api/discord/discord-wrapper"
import { backendAPI } from "~/api/backend-wrapper"
import { useBotContext } from "~/contexts/BotContext"
import type { YoutubeVideo } from "~/api/youtube/youtube-types"
import type { DiscordGuildQueueItem } from "~/api/backend-types"


interface SkeletonQueueItem {
    id: string
    isSkeleton: true
    video: Pick<YoutubeVideo, "youtube_id">
}
type QueueItem = DiscordGuildQueueItem | SkeletonQueueItem

interface PlaybackContextType {
    video: YoutubeVideo | null
    videoLoading: boolean
    playError: string | null
    queue: QueueItem[]
    SongOnClick: (item: YoutubeVideo) => void
    nextQueue: () => void
    stopCurrent: () => void
    popQueue: (index: number) => void
    playFromQueue: (index: number) => void
    reorderQueue: (fromIndex: number, toIndex: number) => void
}

const PlaybackContext = createContext<PlaybackContextType>({
    video: null,
    videoLoading: false,
    playError: null,
    queue: [],
    SongOnClick: () => {},
    nextQueue: () => {},
    stopCurrent: () => {},
    popQueue: () => {},
    playFromQueue: () => {},
    reorderQueue: () => {},
})

export function PlaybackProvider({ children }: { children: ReactNode }) {
    const [searchParams] = useSearchParams()
    const { guildID, botInChannel } = useBotContext()

    const videoId = searchParams.get("v")
    const volume = Number(searchParams.get("vol") ?? 0.5)

    const [video, setVideo] = useState<YoutubeVideo | null>(null)
    const [videoLoading, setVideoLoading] = useState(false)
    const [playError, setPlayError] = useState<string | null>(null)
    const [queue, setQueue] = useState<QueueItem[]>([])

    const refreshQueue = async () => {
        if (!guildID) return
        const data = await backendAPI.queue.get(guildID)
        setQueue(data.items)
    }

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

    useEffect(() => {
        if (!guildID || !botInChannel || videoId) return
        discordBotAPI.musicControl.status(guildID).then(async status => {
            if (!status.playing || !status.video_id) return
            const fetchedVideo = await youtubeAPI.video.retrieve(status.video_id)
            setVideo(fetchedVideo)
        }).catch(() => {})
    }, [guildID, botInChannel])

    useEffect(() => {
        refreshQueue()
    }, [guildID])

    async function playNext() {
        if (!guildID) return
        const data = await backendAPI.queue.get(guildID)
        const next = data.items[0]
        if (!next) {
            setVideo(null)
            return
        }
        setVideoLoading(true)
        await discordBotAPI.musicControl.play(guildID, next.video.youtube_id, 0, volume)
        await backendAPI.queue.removeItem(guildID, next.id)
        setVideo(next.video)
        setVideoLoading(false)
        setQueue(prev => prev.slice(1))
    }

    async function SongOnClick(item: YoutubeVideo) {
        if (!guildID) return

        const skeletonId = `skeleton-${item.youtube_id}-${Date.now()}`
        const skeleton: SkeletonQueueItem = {
            id: skeletonId,
            isSkeleton: true,
            video: { youtube_id: item.youtube_id }   // <-- fixed double brace typo
        }

        if (video) {
            setQueue(prev => [...prev, skeleton])
        }

        try {
            await backendAPI.queue.addItem(guildID, item.youtube_id)
            if (!video) {
                await playNext()
            } else {
                await refreshQueue()
            }
        } catch {
            setQueue(prev => prev.filter(q => q.id !== skeletonId))
        }
    }

    async function nextQueue() {
        if (!guildID) return
        await discordBotAPI.musicControl.stop(guildID)
        await playNext()
    }

    async function popQueue(index: number) {
        if (!guildID) return
        const item = queue[index]
        if (!item) return

        // Don't try to delete a skeleton from the backend
        if ('isSkeleton' in item) {
            setQueue(prev => prev.filter((_, i) => i !== index))
            return
        }

        setQueue(prev => prev.filter((_, i) => i !== index))
        try {
            await backendAPI.queue.removeItem(guildID, item.id)
        } catch {
            await refreshQueue()
        }
    }

    async function playFromQueue(index: number) {
        if (!guildID) return
        const item = queue[index]
        if (!item) return

        // Can't play a skeleton — data isn't ready yet
        if ('isSkeleton' in item) return

        setVideoLoading(true)
        await discordBotAPI.musicControl.stop(guildID)
        await discordBotAPI.musicControl.play(guildID, item.video.youtube_id, 0, volume)
        await backendAPI.queue.removeItem(guildID, item.id)
        setVideo(item.video)
        setQueue(prev => prev.filter((_, i) => i !== index))
        setVideoLoading(false)
    }

    async function reorderQueue(fromIndex: number, toIndex: number) {
        if (!guildID) return
        setQueue(prev => {
            const next = [...prev]
            const [moved] = next.splice(fromIndex, 1)
            next.splice(toIndex, 0, moved)
            return next
        })

        const realIds = queue
            .filter((q): q is DiscordGuildQueueItem => !('isSkeleton' in q))
            .map(q => q.id)

        await backendAPI.queue.reorder(guildID, realIds).catch(() => refreshQueue())
    }

    async function stopCurrent() {
        if (!guildID) return

        try {
            await discordBotAPI.musicControl.stop(guildID)
        } catch {
        }

        setVideo(null)
        setVideoLoading(false)
    }

    return (
        <PlaybackContext.Provider value={{ video, videoLoading, playError, queue, SongOnClick, nextQueue, stopCurrent, popQueue, playFromQueue, reorderQueue }}>
            {children}
        </PlaybackContext.Provider>
    )
}

export const usePlayback = () => useContext(PlaybackContext)

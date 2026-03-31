import { createContext, useContext, useEffect, useState, type ReactNode } from "react"
import { backendAPI } from "~/api/backend-wrapper"
import { useBotContext } from "~/contexts/BotContext"
import { useSocketContext } from "~/contexts/SocketContext"
import type { DiscordGuildQueueItem } from "~/api/backend-types"
import type { YoutubeVideo } from "~/api/youtube/youtube-types"

interface SkeletonQueueItem {
    id: string
    isSkeleton: true
    video: Pick<YoutubeVideo, "youtube_id">
}

export type QueueItem = DiscordGuildQueueItem | SkeletonQueueItem

interface PlaybackQueueContextType {
    queue: QueueItem[]
    queueAdd: (item: YoutubeVideo, playingNow: boolean) => Promise<void>
    queueNext: () => Promise<void>
    queueRemove: (index: number) => Promise<void>
    queuePlayFrom: (index: number) => Promise<YoutubeVideo | null>
    queueSwap: (fromIndex: number, toIndex: number) => Promise<void>
}

const PlaybackQueueContext = createContext<PlaybackQueueContextType>({
    queue: [],
    queueAdd: async () => {},
    queueNext: async () => {},
    queueRemove: async () => {},
    queuePlayFrom: async () => null,
    queueSwap: async () => {},
})

export function PlaybackQueueProvider({ children }: { children: ReactNode }) {
    const { guildID } = useBotContext()
    const { send } = useSocketContext()

    const [queue, setQueue] = useState<QueueItem[]>([])

    // ---- sync ----

    const refreshQueue = async () => {
        if (!guildID) return
        const data = await backendAPI.queue.get(guildID)
        setQueue(data.items)
    }

    useEffect(() => {
        refreshQueue()
    }, [guildID])

    // ---- actions ----

    async function queueAdd(item: YoutubeVideo, playingNow: boolean) {
        if (!guildID) return

        // if something is already playing, add to queue optimistically
        if (playingNow) {
            const skeleton: SkeletonQueueItem = {
                id: `skeleton-${item.youtube_id}-${Date.now()}`,
                isSkeleton: true,
                video: { youtube_id: item.youtube_id },
            }
            setQueue(prev => [...prev, skeleton])
            try {
                await backendAPI.queue.addItem(guildID, item.youtube_id)
                await refreshQueue()
            } catch {
                setQueue(prev => prev.filter(q => q.id !== skeleton.id))
            }
        } else {
            await backendAPI.queue.addItem(guildID, item.youtube_id)
            await refreshQueue()
        }
    }

    async function queueNext(): Promise<void> {
        if (!guildID) return
        const data = await backendAPI.queue.get(guildID)
        const next = data.items[0]
        if (!next) return

        send({ type: "play", video_id: next.video.youtube_id, offset: 0, volume: 0.5 })
        await backendAPI.queue.removeItem(guildID, next.id)
        setQueue(prev => prev.slice(1))
    }

    async function queueRemove(index: number) {
        if (!guildID) return
        const item = queue[index]
        if (!item) return

        setQueue(prev => prev.filter((_, i) => i !== index))

        if ('isSkeleton' in item) return  // skeleton has no backend record

        try {
            await backendAPI.queue.removeItem(guildID, item.id)
        } catch {
            await refreshQueue()
        }
    }

    // plays item at index, removes it from queue, returns the video so
    // PlaybackVideoContext can set it without knowing about the queue internals
    async function queuePlayFrom(index: number): Promise<YoutubeVideo | null> {
        if (!guildID) return null
        const item = queue[index]
        if (!item || 'isSkeleton' in item) return null

        send({ type: "play", video_id: item.video.youtube_id, offset: 0, volume: 0.5 })
        await backendAPI.queue.removeItem(guildID, item.id)
        setQueue(prev => prev.filter((_, i) => i !== index))

        return item.video
    }

    async function queueSwap(fromIndex: number, toIndex: number) {
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

    return (
        <PlaybackQueueContext.Provider value={{ queue, queueAdd, queueNext, queueRemove, queuePlayFrom, queueSwap }}>
            {children}
        </PlaybackQueueContext.Provider>
    )
}

export const usePlaybackQueueContext = () => useContext(PlaybackQueueContext)

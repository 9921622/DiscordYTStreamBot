import { createContext, useContext, useEffect, useState, type ReactNode } from "react"
import { backendAPI } from "~/api/backend-wrapper"
import { useBotContext } from "~/contexts/BotContext"
import { useSocketContext } from "~/contexts/SocketContext"
import type { DiscordGuildQueueItem, DiscordGuildQueue } from "~/api/backend-types"
import type { YoutubeVideo } from "~/api/youtube/youtube-types"
import { usePlaybackVideoContext } from "./PlaybackVideoContext"

interface SkeletonQueueItem {
    id: string
    isSkeleton: true
    video: Pick<YoutubeVideo, "youtube_id">
}

interface QueueResponse {
    queue?: DiscordGuildQueue
    error?: string
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
    const { guildID, botInChannel } = useBotContext()
    const { videoPlay } = usePlaybackVideoContext()
    const { send, on, connected } = useSocketContext()
    const [queue, setQueue] = useState<QueueItem[]>([])

    // ---- sync ----
    useEffect(() => on("queue-get",     (data) => { const d = data as QueueResponse; if (d.queue) setQueue(d.queue.items) }), [on])
    useEffect(() => on("queue-add",     (data) => { const d = data as QueueResponse; if (!d.error && d.queue) setQueue(d.queue.items) }), [on])
    useEffect(() => on("queue-remove",  (data) => { const d = data as QueueResponse; if (!d.error && d.queue) setQueue(d.queue.items) }), [on])
    useEffect(() => on("queue-reorder", (data) => { const d = data as QueueResponse; if (!d.error && d.queue) setQueue(d.queue.items) }), [on])
    useEffect(() => on("queue-clear",   (data) => { const d = data as QueueResponse; if (!d.error) setQueue([]) }), [on])

    useEffect(() => {
        if (!guildID || !botInChannel || !connected) return
        send({ type: "queue-get" })
    }, [guildID, botInChannel, connected])

    // ---- actions ----

    async function queueAdd(item: YoutubeVideo, playingNow: boolean) {
        if (!guildID || !botInChannel) return

        const nothingPlaying = !playingNow && queue.length === 0
        if (nothingPlaying) {
            videoPlay(item)
            return
        }

        if (playingNow) {
            const skeleton: SkeletonQueueItem = {
                id: `skeleton-${item.youtube_id}-${Date.now()}`,
                isSkeleton: true,
                video: { youtube_id: item.youtube_id },
            }
            setQueue(prev => [...prev, skeleton])
        }
        send({ type: "queue-add", youtube_id: item.youtube_id })
    }

    async function queueNext(): Promise<void> {
        if (!guildID || !botInChannel) return
        const next = queue[0]
        if (!next || 'isSkeleton' in next) return
        videoPlay(next.video);
        send({ type: "queue-remove", item_id: next.id })
    }

    async function queueRemove(index: number) {
        if (!guildID || !botInChannel) return
        const item = queue[index]
        if (!item) return
        if ('isSkeleton' in item) {
            setQueue(prev => prev.filter((_, i) => i !== index))
            return
        }
        setQueue(prev => prev.filter((_, i) => i !== index))  // optimistic
        send({ type: "queue-remove", item_id: item.id })
    }

    async function queuePlayFrom(index: number): Promise<YoutubeVideo | null> {
        if (!guildID || !botInChannel) return null
        const item = queue[index]
        if (!item || 'isSkeleton' in item) return null
        videoPlay(item.video);
        send({ type: "queue-remove", item_id: item.id })
        setQueue(prev => prev.filter((_, i) => i !== index))
        return item.video
    }

    async function queueSwap(fromIndex: number, toIndex: number) {
        if (!guildID || !botInChannel) return
        const reordered = [...queue]
        const [moved] = reordered.splice(fromIndex, 1)
        reordered.splice(toIndex, 0, moved)
        setQueue(reordered)  // optimistic
        const realIds = reordered
            .filter((q): q is DiscordGuildQueueItem => !('isSkeleton' in q))
            .map(q => q.id)
        send({ type: "queue-reorder", order: realIds })
    }

    return (
        <PlaybackQueueContext.Provider value={{ queue, queueAdd, queueNext, queueRemove, queuePlayFrom, queueSwap }}>
            {children}
        </PlaybackQueueContext.Provider>
    )
}
export const usePlaybackQueueContext = () => useContext(PlaybackQueueContext)

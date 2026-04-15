import { createContext, useContext, useEffect, useState, type ReactNode } from "react"
import { useBotContext } from "~/contexts/BotContext"
import { useSocketContext } from "~/contexts/SocketContext"
import type { DiscordUser, DiscordGuildPlaylistItem, DiscordGuildPlaylist } from "~/api/backend-types"
import type { YoutubeVideo } from "~/api/youtube/youtube-types"
import type { WSResponse } from "~/api/backend-types"
import { useUser } from "./UserContext"

/*
    for queue manipulation (add, remove, reorder) and tracking current video (for now playing, sync checks)
*/

interface SkeletonQueueItem {
    id: string
    isSkeleton: true
    video: Pick<YoutubeVideo, "youtube_id">
}

export type QueueItem = DiscordGuildPlaylistItem | SkeletonQueueItem

interface PlaylistContextType {
    playlist: DiscordGuildPlaylist | null
    queue: QueueItem[]
    currentVideo: YoutubeVideo | null
    currentVideoLoading: boolean
    currentAddedBy: DiscordUser | null
    setCurrentVideo: (video: YoutubeVideo | null) => void
    add: (item: YoutubeVideo) => void
    playNow: (item: YoutubeVideo | DiscordGuildPlaylistItem) => void
    remove: (index: number) => void
    reorder: (fromIndex: number, toIndex: number) => void
    clear: () => void
    next: () => void
    prev: () => void
}

const PlaylistContext = createContext<PlaylistContextType>({
    playlist: null,
    queue: [],
    currentVideo: null,
    currentVideoLoading: false,
    currentAddedBy: null,
    setCurrentVideo: () => {},
    add: () => {},
    playNow: () => {},
    remove: () => {},
    reorder: () => {},
    clear: () => {},
    next: () => {},
    prev: () => {},
})

export function PlaylistProvider({ children }: { children: ReactNode }) {
    const discordUser = useUser()
    const { guildID, botInChannel } = useBotContext()
    const { send, on, connected } = useSocketContext()

    const [playlist, setPlaylist] = useState<DiscordGuildPlaylist | null>(null)
    const [skeletons, setSkeletons] = useState<SkeletonQueueItem[]>([])

    const [currentVideo, setCurrentVideo] = useState<YoutubeVideo | null>(null)
    const [currentVideoLoading, setCurrentVideoLoading] = useState(false)
    const [currentAddedBy, setCurrentAddedBy] = useState<DiscordUser | null>(null)

    const realItems = playlist?.items ?? []
    const pendingSkeletons = skeletons.filter(
        s => !realItems.some(item => item.video.youtube_id === s.video.youtube_id)
    )
    const queue: QueueItem[] = [...realItems, ...pendingSkeletons]

    function applyPlaylistResponse(resp: WSResponse) {
        if (!resp.success) return
        const incoming = resp.data?.playlist as DiscordGuildPlaylist | undefined
        if (!incoming) return

        setPlaylist(incoming)
        setSkeletons(prev =>
            prev.filter(s => !incoming.items.some(item => item.video.youtube_id === s.video.youtube_id))
        )

        setCurrentVideo((incoming.current_item?.video as YoutubeVideo) ?? null)
        setCurrentVideoLoading(incoming.current_item?.video === null)
    }

    function resetAll() {
        setPlaylist(null)
        setSkeletons([])
        setCurrentVideo(null)
        setCurrentAddedBy(null)
    }

    useEffect(() => on("on_disconnect", (resp: WSResponse) => {
        if (!resp.success) return
        resetAll()
    }), [on])

    useEffect(() => on("queue-get",     applyPlaylistResponse), [on])
    useEffect(() => on("queue-add",     applyPlaylistResponse), [on])
    useEffect(() => on("queue-remove",  applyPlaylistResponse), [on])
    useEffect(() => on("queue-reorder", applyPlaylistResponse), [on])
    useEffect(() => on("queue-next",    applyPlaylistResponse), [on])
    useEffect(() => on("queue-prev",    applyPlaylistResponse), [on])

    useEffect(() => on("play", (resp: WSResponse) => {
        setCurrentVideoLoading(false)
        if (!resp.success) return
        applyPlaylistResponse(resp)
        const addedBy = resp.data?.playlist?.current_item?.added_by as DiscordUser | undefined
        setCurrentAddedBy(addedBy ?? null)
    }), [on])

    useEffect(() => on("play_now", (resp: WSResponse) => {
        setCurrentVideoLoading(false)
        if (!resp.success) return
        applyPlaylistResponse(resp)
        const addedBy = resp.data?.playlist?.current_item?.added_by as DiscordUser | undefined
        setCurrentAddedBy(addedBy ?? null)
    }), [on])

    useEffect(() => on("queue-clear", (resp: WSResponse) => {
        if (!resp.success) return
        resetAll()
    }), [on])

    useEffect(() => on("stop", (resp: WSResponse) => {
        if (!resp.success) return
        setCurrentVideo(null)
        setCurrentVideoLoading(false)
        setCurrentAddedBy(null)
    }), [on])

    useEffect(() => on("song_end", (resp: WSResponse) => {
        if (!resp.success) return
        setCurrentVideo(null)
        setCurrentVideoLoading(false)
        setCurrentAddedBy(null)
    }), [on])

    function canAct() {
        return !!(guildID && botInChannel && discordUser && connected)
    }

    useEffect(() => {
        if (!canAct() || !discordUser) return
        send({ type: "queue-get", discord_id: discordUser.discord_id })
    }, [guildID, botInChannel, connected])

    function add(item: YoutubeVideo) {
        if (!canAct()) return
        setSkeletons(prev => [...prev, {
            id: `skeleton-${item.youtube_id}-${Date.now()}`,
            isSkeleton: true,
            video: { youtube_id: item.youtube_id },
        }])
        send({ type: "queue-add", youtube_id: item.youtube_id, discord_id: discordUser!.discord_id })
    }

    function playNow(item: YoutubeVideo | DiscordGuildPlaylistItem) {
        if (!canAct()) return
        setCurrentVideo(null)
        setCurrentVideoLoading(true)

        if ("youtube_id" in item) {
            // YoutubeVideo — add and play
            send({ type: "play_now", video_id: item.youtube_id, discord_id: discordUser!.discord_id })
        } else {
            // DiscordGuildPlaylistItem — jump to existing item
            send({ type: "play_now", item_id: item.id, discord_id: discordUser!.discord_id })
        }
    }

    function remove(index: number) {
        if (!canAct()) return
        const item = queue[index]
        if (!item) return
        if ("isSkeleton" in item) {
            setSkeletons(prev => prev.filter((_, i) => i !== index))
            return
        }
        setPlaylist(prev => prev ? { ...prev, items: prev.items.filter(i => i.id !== item.id) } : prev)
        send({ type: "queue-remove", item_id: item.id, discord_id: discordUser!.discord_id })
    }

    function reorder(fromIndex: number, toIndex: number) {
        if (!canAct() || !playlist) return
        const reordered = [...playlist.items]
        const [moved] = reordered.splice(fromIndex, 1)
        reordered.splice(toIndex, 0, moved)
        setPlaylist(prev => prev ? { ...prev, items: reordered } : prev)
        send({ type: "queue-reorder", order: reordered.map(q => q.id), discord_id: discordUser!.discord_id })
    }

    function clear() {
        if (!canAct()) return
        send({ type: "queue-clear", discord_id: discordUser!.discord_id })
    }

    function next() {
        if (!canAct()) return
        setCurrentVideo(null)
        setCurrentVideoLoading(true)
        send({ type: "queue-next", discord_id: discordUser!.discord_id })
    }

    function prev() {
        if (!canAct()) return
        setCurrentVideo(null)
        setCurrentVideoLoading(true)
        send({ type: "queue-prev", discord_id: discordUser!.discord_id })
    }

    return (
        <PlaylistContext.Provider value={{
            playlist, queue,
            currentVideo, currentVideoLoading, currentAddedBy,
            setCurrentVideo,
            add, playNow, remove, reorder, clear, next, prev,
        }}>
            {children}
        </PlaylistContext.Provider>
    )
}

export const usePlaylistContext = () => useContext(PlaylistContext)

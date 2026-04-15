import { createContext, useContext, useEffect, useState } from "react"
import type { ReactNode } from "react"
import { useBotContext } from "./BotContext"
import { useSocketContext } from "./SocketContext"
import type { WSResponse } from "~/api/backend-types"
import { useUser } from "./UserContext"


/*
    for controls like pause, volume, loop (things that send commands)
*/

interface PlaybackStatusContextType {
    video_id: string | null
    playing: boolean
    paused: boolean
    position: number
    duration: number
    sourceUrl: string | null
    volume: number
    ended: boolean
    loop: boolean
    resetStatus: () => void
    videoPause: () => void
    videoVolume: (level: number) => void
    videoLoop: () => void
}

const DEFAULT_VOLUME = 0.5

const PlaybackStatusContext = createContext<PlaybackStatusContextType>({
    video_id: "",
    playing: false,
    paused: false,
    position: 0,
    duration: 0,
    sourceUrl: null,
    volume: DEFAULT_VOLUME,
    ended: false,
    loop: false,
    resetStatus: () => {},
    videoPause: () => {},
    videoVolume: () => {},
    videoLoop: () => {},
})

export function PlaybackStatusProvider({ children }: { children: ReactNode }) {
    const discordUser = useUser()
    const { send, on, connected } = useSocketContext()
    const { botInChannel } = useBotContext()

    const [video_id, setVideoID] = useState<string | null>(null)
    const [playing, setPlaying] = useState(false)
    const [paused, setPaused] = useState(false)
    const [position, setPosition] = useState(0)
    const [sourceUrl, setSourceUrl] = useState<string | null>(null)
    const [volume, setVolume] = useState(DEFAULT_VOLUME)
    const [ended, setEnded] = useState(false)
    const [loop, setLoop] = useState(false)
    const [duration, setDuration] = useState(100)

    useEffect(() => {
        if (!botInChannel || !discordUser) return
        send({ type: "status", discord_id: discordUser.discord_id })
    }, [botInChannel, connected])

    // ==============================================================================

    function resetStatus() {
        setVideoID(null)
        setPlaying(false)
        setPaused(false)
        setPosition(0)
        setSourceUrl(null)
        setEnded(false)
    }

    useEffect(() => on("on_disconnect", (resp: WSResponse) => {
        if (!resp.success) return
        resetStatus()
    }), [on])

    function applyPlaylistResponse(resp: WSResponse) {
        if (!resp.success) return
        const incoming = resp.data?.playlist?.current_item?.video?.duration;
        if (incoming)
            setDuration(incoming)
    }
    useEffect(() => on("queue-get",     applyPlaylistResponse), [on])
    useEffect(() => on("queue-add",     applyPlaylistResponse), [on])
    useEffect(() => on("queue-remove",  applyPlaylistResponse), [on])
    useEffect(() => on("queue-reorder", applyPlaylistResponse), [on])
    useEffect(() => on("queue-next",    applyPlaylistResponse), [on])
    useEffect(() => on("queue-prev",    applyPlaylistResponse), [on])
    useEffect(() => on("play",          applyPlaylistResponse), [on])

    function get_status(resp: WSResponse) {
        if (!resp.success || !resp.data) return
        const s = resp.data.playback
        setVideoID(s.video_id ?? null)
        setPlaying(s.playing ?? false)
        setPaused(s.paused ?? false)
        setPosition(s.position ?? 0)
        setSourceUrl(s.source_url ?? null)
        setVolume(s.volume ?? DEFAULT_VOLUME)
        setEnded(s.ended ?? false)
        setLoop(s.loop ?? false)
    }

    useEffect(() => on("status", (resp: WSResponse) => {
        get_status(resp)
    }), [on])

    useEffect(() => on("stop", (resp: WSResponse) => {
        if (!resp.success) return
        resetStatus()
    }), [on])

    useEffect(() => on("song_start", (resp: WSResponse) => {
        get_status(resp)
    }), [on])

    useEffect(() => on("song_end", (resp: WSResponse) => {
        if (!resp.success) return
        resetStatus()
    }), [on])

    useEffect(() => on("pause", (resp: WSResponse) => {
        if (!resp.success || !resp.data) return
        const { paused } = resp.data
        if (typeof paused !== "boolean") return
        setPaused(paused)
    }), [on])

    useEffect(() => on("volume", (resp: WSResponse) => {
        if (!resp.success || !resp.data) return
        const { volume } = resp.data
        if (typeof volume !== "number") return
        setVolume(volume)
    }), [on])

    useEffect(() => on("loop", (resp: WSResponse) => {
        if (!resp.success || !resp.data) return
        const { loop } = resp.data
        if (typeof loop !== "boolean") return
        setLoop(loop)
    }), [on])

    // ==============================================================================

    function videoPause() {
        if (!botInChannel || !discordUser) return
        send({ type: "pause", discord_id: discordUser.discord_id })
    }

    function videoVolume(level: number) {
        if (!botInChannel || !discordUser) return
        setVolume(level) // optimistic
        send({ type: "volume", discord_id: discordUser.discord_id, level })
    }

    function videoLoop() {
        if (!botInChannel || !discordUser) return
        send({ type: "loop", discord_id: discordUser.discord_id })
    }

    return (
        <PlaybackStatusContext.Provider value={{
            video_id, playing, paused, position, duration, sourceUrl, volume, ended, loop,
            resetStatus,
            videoPause, videoVolume, videoLoop,
        }}>
            {children}
        </PlaybackStatusContext.Provider>
    )
}

export const usePlaybackStatusContext = () => useContext(PlaybackStatusContext)

import React, { forwardRef, useEffect, useRef, useState } from "react"
import type { YoutubeVideo } from "~/api/youtube/youtube-types"
import { createPortal } from "react-dom"
import { Heart, Plus } from "lucide-react"
import { PlayPauseIcon } from "./utilities/Icons"
import { useCurrentPlayback } from "~/hooks/useCurrentPlayback"
import { usePlaylistContext } from "~/contexts/PlaylistContext"
import { usePlaybackStatusContext } from "~/contexts/PlaybackStatusContext"

type SongContextMenuHelperProps = {
    x: number
    y: number
    song: YoutubeVideo
    onClose: () => void
}

const SongContextMenuHelper = forwardRef<HTMLUListElement, SongContextMenuHelperProps>(
    ({ x, y, song, onClose }, ref) => {
        const iconClass = "w-4 h-4 text-white"
        const { add, playNow } = usePlaylistContext()
        const { videoPause } = usePlaybackStatusContext()
        const { isPlaying, currentItem } = useCurrentPlayback()

        const isCurrentSong = currentItem?.video?.youtube_id === song.youtube_id
        const isThisSongPlaying = isCurrentSong && isPlaying

        const options: { label: React.ReactNode; action: () => void }[] = [
            {
                label: (
                    <span className="flex items-center gap-2">
                        <PlayPauseIcon isPlaying={isThisSongPlaying} />
                        {isThisSongPlaying ? "Pause" : "Play"}
                    </span>
                ),
                action: () => {
                    if (isCurrentSong)
                        videoPause()
                    else
                        playNow(song)
                    onClose()
                }
            },
            {
                label: <span className="flex items-center gap-2"><Plus className={iconClass} /> Add to Queue</span>,
                action: () => { add(song); onClose() }
            },
            {
                label: <span className="flex items-center gap-2"><Heart className={iconClass} /> Add to Likes</span>,
                action: () => { onClose() }
            },
        ]

        return (
            <ul
                ref={ref}
                data-portal
                className="fixed z-50 bg-zinc-800 border border-zinc-700 rounded-md shadow-lg py-1 w-44"
                style={{ top: y, left: x }}
            >
                {options.map((opt, i) => (
                    <li
                        key={song.youtube_id + i}
                        className="px-4 py-2 text-sm text-zinc-200 hover:bg-zinc-700 cursor-pointer"
                        onClick={opt.action}
                    >
                        {opt.label}
                    </li>
                ))}
            </ul>
        )
    }
)

type SongContextMenuProps = {
    song: YoutubeVideo
    children: React.ReactNode
}

export default function SongContextMenu({ song, children }: SongContextMenuProps) {
    const [menu, setMenu] = useState<{ x: number; y: number } | null>(null)
    const menuRef = useRef<HTMLUListElement | null>(null)

    function onContextMenu(e: React.MouseEvent) {
        e.preventDefault()
        setMenu({
            x: Math.min(e.clientX, window.innerWidth - 180),
            y: Math.min(e.clientY, window.innerHeight - 140),
        })
    }

    useEffect(() => {
        if (!menu) return
        function handleClick(e: MouseEvent) {
            if (menuRef.current && !menuRef.current.contains(e.target as Node))
                setMenu(null)
        }
        window.addEventListener("mousedown", handleClick)
        return () => window.removeEventListener("mousedown", handleClick)
    }, [menu])

    return (
        <>
            <div onContextMenu={onContextMenu}>
                {children}
            </div>
            {menu && createPortal(
                <SongContextMenuHelper
                    ref={menuRef}
                    x={menu.x}
                    y={menu.y}
                    song={song}
                    onClose={() => setMenu(null)}
                />,
                document.body
            )}
        </>
    )
}

import React, { forwardRef, useEffect, useRef, useState } from "react";
import type { YoutubeVideo } from "~/api/youtube/youtube-types";
import { usePlaybackQueueContext } from "~/contexts/PlaybackQueueContext";
import { usePlaybackVideoContext } from "~/contexts/PlaybackVideoContext";
import { CrossIcon, HeartIcon, PlayIcon } from "./utilities/Icons";
import { createPortal } from "react-dom";

type SongContextMenuProps = {
    x: number
    y: number
    song: YoutubeVideo
    onClose: () => void
}

const SongContextMenu = forwardRef<HTMLUListElement, SongContextMenuProps>(
    ({ x, y, song, onClose }, ref) => {
        const { videoPlay, videoPlaybackStatus } = usePlaybackVideoContext()
        const { queueAdd } = usePlaybackQueueContext()

        const options: {label: React.ReactNode; action: () => void }[] = [
            {
                label: <span className="flex items-center gap-2"><PlayIcon /> Play</span>,
                action: () => { videoPlay(song); onClose() }
            },
            {
                label: <span className="flex items-center gap-2"><CrossIcon /> Add to Queue</span>,
                action: () => { queueAdd(song, !!videoPlaybackStatus?.playing); onClose() }
            },
            {
                label: <span className="flex items-center gap-2"><HeartIcon /> Add to Likes</span>,
                action: () => { onClose() }
            },
        ]

        return (
            <ul
                ref={ref}
                className="fixed z-50 bg-zinc-800 border border-zinc-700 rounded-md shadow-lg py-1 w-44"
                style={{ top: y, left: x }}>

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

type SongDropdownProps = {
    song: YoutubeVideo
    children: React.ReactNode
}

export default function SongDropdown({ song, children }: SongDropdownProps) {
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
            if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
                setMenu(null)
            }
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
                <SongContextMenu
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

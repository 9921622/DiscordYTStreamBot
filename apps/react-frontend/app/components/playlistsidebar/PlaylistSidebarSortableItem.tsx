import { Play, Pause } from "lucide-react"
import { CSS } from "@dnd-kit/utilities"
import { useSortable } from "@dnd-kit/sortable"
import type { QueueItem } from "~/contexts/PlaylistContext"
import { DragHandle, EqualizerBars } from "../utilities/Icons"
import MemberAvatar from "../MemberAvatar"
import { useCurrentPlayback } from "~/hooks/useCurrentPlayback"

interface Props {
    item: QueueItem
    index: number
    onPlay: () => void
    onRemove: (e: React.MouseEvent) => void
}

function SkeletonRow() {
    return (
        <>
            <div className="w-20 h-20 rounded bg-zinc-700 animate-pulse flex-shrink-0" />
            <div className="flex-1 min-w-0 flex flex-col gap-1.5">
                <div className="h-3 bg-zinc-700 animate-pulse rounded w-3/4" />
                <div className="h-2.5 bg-zinc-800 animate-pulse rounded w-1/2" />
            </div>
        </>
    )
}

function RealRow({ item, isActive, isCurrentlyPlaying, isPaused, onRemove }: {
    item: Exclude<QueueItem, { isSkeleton: true }>
    isActive: boolean
    isCurrentlyPlaying: boolean
    isPaused: boolean
    onRemove: (e: React.MouseEvent) => void
}) {
    return (
        <>
            <div className="relative w-20 h-20 flex-shrink-0">
                <img
                    src={item.video.thumbnail ?? ""}
                    alt={item.video.title}
                    className={`w-full h-full rounded object-cover transition ${isPaused ? "opacity-50" : ""}`}
                />
                {isCurrentlyPlaying && !isPaused ? (
                    <div className="absolute inset-0 bg-black/40 flex items-center justify-center rounded">
                        <EqualizerBars />
                    </div>
                ) : isActive ? (
                    <div className="absolute inset-0 bg-black/40 flex items-center justify-center rounded">
                        <Pause className="w-4 h-4 text-white" />
                    </div>
                ) : (
                    <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 flex items-center justify-center rounded transition">
                        <Play className="w-4 h-4 text-white" />
                    </div>
                )}
                {item.added_by && (
                    <div className="absolute -top-2 -left-2">
                        <MemberAvatar
                            src={item.added_by.avatar_url}
                            alt={item.added_by.username}
                            tooltip={item.added_by.global_name}
                            size={20}
                            className="ring-1 ring-zinc-900 group-hover:brightness-50"
                        />
                    </div>
                )}
            </div>

            <div className="flex-1 min-w-0">
                <p className={`text-sm truncate ${isActive ? isPaused ? "text-green-400/50" : "text-green-400" : "text-white"}`}>
                    {item.video.title}
                </p>
                <p className="text-zinc-400 text-xs truncate">{item.video.creator}</p>
            </div>

            {isActive ? (
                <span className={`text-xs font-medium shrink-0 ${isPaused ? "text-green-400/50" : "text-green-400"}`}>
                    {isPaused ? "paused" : "playing"}
                </span>
            ) : (
                <button
                    className="btn btn-ghost btn-xs opacity-0 group-hover:opacity-100 text-zinc-400 hover:text-red-400"
                    onClick={onRemove}
                >
                    ✕
                </button>
            )}
        </>
    )
}

export default function SortableItem({ item, index, onPlay, onRemove }: Props) {
    const isSkeleton = "isSkeleton" in item
    const { isPlaying, isPaused, currentItem } = useCurrentPlayback()

    const isCurrentlyPlaying = !isSkeleton && isPlaying && item.id === currentItem?.id
    const isCurrentlyPaused = !isSkeleton && isPaused && item.id === currentItem?.id
    const isActive = isCurrentlyPlaying || isCurrentlyPaused

    const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
        useSortable({ id: item.id, disabled: isSkeleton })

    const style = {
        transform: CSS.Transform.toString(transform),
        transition,
        opacity: isDragging ? 0.4 : 1,
        zIndex: isDragging ? 50 : undefined,
    }

    return (
        <li
            ref={setNodeRef}
            style={style}
            className={`flex items-center gap-3 px-4 py-3 group
                ${isSkeleton  ? "opacity-60 cursor-wait"
                : isActive    ? "bg-zinc-800/80 cursor-default"
                : isDragging  ? "bg-zinc-800"
                :                "hover:bg-zinc-800 cursor-pointer"}
            `}
            onClick={() => !isSkeleton && !isActive && onPlay()}>
            {!isSkeleton && (
                <span
                    className="opacity-0 group-hover:opacity-100 cursor-grab active:cursor-grabbing transition"
                    {...attributes}
                    {...listeners}
                    onClick={e => e.stopPropagation()}
                >
                    <DragHandle />
                </span>
            )}

            <span className="text-zinc-500 text-xs w-4">{index + 1}</span>

            {isSkeleton ? (
                <SkeletonRow />
            ) : (
                <RealRow
                    item={item}
                    isActive={isActive}
                    isCurrentlyPlaying={isCurrentlyPlaying}
                    isPaused={isCurrentlyPaused}
                    onRemove={onRemove}
                />
            )}
        </li>
    )
}

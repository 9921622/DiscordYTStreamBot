import { Play } from "lucide-react"
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

function RealRow({ item, isCurrentlyPlaying, onRemove }: {
    item: Exclude<QueueItem, { isSkeleton: true }>
    isCurrentlyPlaying: boolean
    onRemove: (e: React.MouseEvent) => void
}) {
    return (
        <>
            <div className="relative w-20 h-20 flex-shrink-0">
                <img
                    src={item.video.thumbnail ?? ""}
                    alt={item.video.title}
                    className="w-full h-full rounded object-cover"
                />
                {isCurrentlyPlaying ? (
                    <div className="absolute inset-0 bg-black/40 flex items-center justify-center rounded">
                        <EqualizerBars />
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
                <p className={`text-sm truncate ${isCurrentlyPlaying ? "text-green-400" : "text-white"}`}>
                    {item.video.title}
                </p>
                <p className="text-zinc-400 text-xs truncate">{item.video.creator}</p>
            </div>

            {isCurrentlyPlaying ? (
                <span className="text-green-400 text-xs font-medium shrink-0">playing</span>
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
    const { isPlaying, currentItem } = useCurrentPlayback()

    const isCurrentlyPlaying = !isSkeleton && isPlaying && item.id === currentItem?.id

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
                ${isSkeleton         ? "opacity-60 cursor-wait"
                : isCurrentlyPlaying ? "bg-zinc-800/80 cursor-default"
                : isDragging         ? "bg-zinc-800"
                :                      "hover:bg-zinc-800 cursor-pointer"}
            `}
            onClick={() => !isSkeleton && !isCurrentlyPlaying && onPlay()}>
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
                    isCurrentlyPlaying={isCurrentlyPlaying}
                    onRemove={onRemove}
                />
            )}
        </li>
    )
}

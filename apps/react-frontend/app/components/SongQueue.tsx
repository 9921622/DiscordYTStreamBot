import { useBotContext } from "~/contexts/BotContext"
import { usePlaybackVideoContext } from "~/contexts/PlaybackVideoContext"
import {
    DndContext,
    closestCenter,
    PointerSensor,
    useSensor,
    useSensors,
    type DragEndEvent,
} from "@dnd-kit/core"
import {
    SortableContext,
    verticalListSortingStrategy,
    useSortable,
    arrayMove,
} from "@dnd-kit/sortable"
import { restrictToVerticalAxis, restrictToFirstScrollableAncestor  } from "@dnd-kit/modifiers"
import { CSS } from "@dnd-kit/utilities"
import { usePlaybackQueueContext } from "~/contexts/PlaybackQueueContext"
import VCMembersContainer from "./VCMembersContainer"
import { ListX, Play, Shuffle, SkipForward, Square } from "lucide-react"

function DragHandle() {
    return (
        <svg className="w-5 h-6 text-zinc-500 flex-shrink-0" fill="currentColor" viewBox="0 0 8 16">
            <circle cx="2" cy="3" r="1.2" /><circle cx="6" cy="3" r="1.2" />
            <circle cx="2" cy="8" r="1.2" /><circle cx="6" cy="8" r="1.2" />
            <circle cx="2" cy="13" r="1.2" /><circle cx="6" cy="13" r="1.2" />
        </svg>
    )
}

function SortableItem({ item, index, onPlay, onRemove }: {
    item: any
    index: number
    onPlay: () => void
    onRemove: (e: React.MouseEvent) => void
}) {
    const thumbnailSize = "w-20 h-20"
    const isSkeleton = 'isSkeleton' in item

    const {
        attributes,
        listeners,
        setNodeRef,
        transform,
        transition,
        isDragging,
    } = useSortable({ id: item.id, disabled: isSkeleton })

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
                ${isSkeleton ? 'opacity-60 cursor-wait' : 'hover:bg-zinc-800 cursor-pointer'}
                ${isDragging ? 'bg-zinc-800' : ''}
            `}
            onClick={() => !isSkeleton && onPlay()}
        >
            {/* Drag handle — only on real items */}
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
                <>
                    <div className={`${thumbnailSize} rounded bg-zinc-700 animate-pulse flex-shrink-0`} />
                    <div className="flex-1 min-w-0 flex flex-col gap-1.5">
                        <div className="h-3 bg-zinc-700 animate-pulse rounded w-3/4" />
                        <div className="h-2.5 bg-zinc-800 animate-pulse rounded w-1/2" />
                    </div>
                </>
            ) : (
                <>
                    <div className={`relative ${thumbnailSize} flex-shrink-0`}>
                        <img
                            src={item.video.thumbnail ?? ""}
                            alt={item.video.title}
                            className="w-full h-full rounded object-cover"
                        />
                        <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 flex items-center justify-center rounded transition">
                            <Play className="w-4 h-4 text-white" />
                        </div>
                        {item.added_by && (
                            <div
                                className="absolute -top-2 -left-2 tooltip tooltip-right"
                                data-tip={item.added_by.global_name ?? item.added_by.username}
                                >
                                <img
                                    src={item.added_by.avatar_url}
                                    alt={item.added_by.username}
                                    className="w-5 h-5 rounded-full object-cover ring-1 ring-zinc-900 group-hover:brightness-50 transition"
                                />
                            </div>
                        )}
                    </div>
                    <div className="flex-1 min-w-0">
                        <p className="text-white text-sm truncate">{item.video.title}</p>
                        <p className="text-zinc-400 text-xs truncate">{item.video.creator}</p>
                    </div>
                    <button
                        className="btn btn-ghost btn-xs opacity-0 group-hover:opacity-100 text-zinc-400 hover:text-red-400"
                        onClick={onRemove}
                    >
                        ✕
                    </button>
                </>
            )}
        </li>
    )
}


function CurrentSong() {
    const thumbnailSize = "w-30 h-30"
    const { video, videoLoading, videoStop } = usePlaybackVideoContext();
    const { queue, queueNext } = usePlaybackQueueContext()

    function clickHandler() {
        if (queue?.length > 0)
            queueNext();
        else
            videoStop();
    }

    return (
        <div className="p-3 border-b border-zinc-800">
            <p className="text-xs text-zinc-400 mb-2">Now Playing</p>

            <div className="flex items-center gap-3 bg-zinc-800/60 rounded-md p-2">

                {videoLoading ? (
                    <>
                        <div className={`skeleton ${thumbnailSize} rounded flex-shrink-0`} />

                        <div className="flex-1 min-w-0 space-y-1">
                            <div className="skeleton h-3 w-3/4" />
                            <div className="skeleton h-3 w-1/2" />
                        </div>

                        <div className="flex gap-[2px] items-end h-4 opacity-50">
                            <div className="skeleton w-[2px] h-2" />
                            <div className="skeleton w-[2px] h-3" />
                            <div className="skeleton w-[2px] h-4" />
                        </div>
                    </>
                ) : video ? (
                    <>
                        <img
                            src={video.thumbnail ?? ""}
                            alt={video.title}
                            className={`${thumbnailSize} rounded object-cover flex-shrink-0`}
                        />

                        <div className="flex-1 min-w-0">
                            <p className="text-white text-sm truncate">{video.title}</p>
                            <p className="text-zinc-400 text-xs truncate">{video.creator}</p>
                        </div>

                        <div className="flex gap-[2px] items-end h-4">
                            <span className="w-[2px] bg-green-400 animate-eq-fast" />
                            <span className="w-[2px] bg-green-400 animate-eq [animation-delay:-0.2s]" />
                            <span className="w-[2px] bg-green-400 animate-eq-slow [animation-delay:-0.4s]" />
                        </div>

                        <button
                            onClick={clickHandler}
                            className="btn btn-xs btn-ghost text-red-400 hover:bg-red-500/20"
                            title="Stop"
                        >
                            {
                                queue?.length > 0 ?
                                <SkipForward className="w-6 h-6 text-white" /> :
                                <Square className="w-6 h-6 text-white" />
                            }

                        </button>
                    </>
                ) : (
                    <p className="text-zinc-500 text-sm">Nothing playing</p>
                )}
            </div>
        </div>
    );
}

export default function QueueSidebar() {
    const { queue, queuePlayFrom, queueRemove, queueSwap, queueClear } = usePlaybackQueueContext();

    const sensors = useSensors(useSensor(PointerSensor, {
        activationConstraint: { distance: 5 }
    }))

    function handleDragEnd(event: DragEndEvent) {
        const { active, over } = event
        if (!over || active.id === over.id) return

        const fromIndex = queue.findIndex(q => q.id === active.id)
        const toIndex = queue.findIndex(q => q.id === over.id)
        if (fromIndex !== -1 && toIndex !== -1) {
            queueSwap(fromIndex, toIndex)
        }
    }

    return (
        <div className="w-112 h-full flex flex-col rounded-lg ml-2">
            <VCMembersContainer/>
            <CurrentSong />

            <div className="p-4 border-b border-zinc-700 flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <p className="font-bold text-white">Queue</p>
                    <span className="badge badge-neutral">{queue.length}</span>
                </div>

                <div className="flex items-center gap-1">
                    <button title="Shuffle" className="btn btn-ghost btn-xs btn-circle hover:bg-zinc-700" onClick={() => {}}>
                        <Shuffle className="w-6 h-6 text-white" />
                    </button>
                    <button title="Clear Queue" className="btn btn-ghost btn-xs btn-circle hover:bg-red-500/20 hover:text-red-400" onClick={queueClear}>
                        <ListX className="w-6 h-6 text-red-400" />
                    </button>
                </div>

            </div>

            {queue.length === 0 ? (
                <div className="flex-1 flex items-center justify-center text-zinc-500 text-sm">
                    Queue is empty
                </div>
            ) : (
                <DndContext
                        sensors={sensors}
                        collisionDetection={closestCenter}
                        onDragEnd={handleDragEnd}
                        modifiers={[restrictToVerticalAxis, restrictToFirstScrollableAncestor ]}>
                    <SortableContext items={queue.map(q => q.id)} strategy={verticalListSortingStrategy}>
                        <ul className="flex-1 overflow-y-auto divide-y divide-zinc-800 pb-[var(--musicbar-height,80px)]">
                            {queue.map((item, index) => (
                                <SortableItem
                                    key={item.id}
                                    item={item}
                                    index={index}
                                    onPlay={() => queuePlayFrom(index)}
                                    onRemove={(e) => { e.stopPropagation(); queueRemove(index) }}
                                />
                            ))}
                        </ul>
                    </SortableContext>
                </DndContext>
            )}
        </div>
    )
}

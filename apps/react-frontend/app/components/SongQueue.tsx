import { useBotContext } from "~/contexts/BotContext"
import { usePlaybackVideoContext } from "~/contexts/PlaybackVideoContext"
import { PlayIcon, StopIcon, NextIcon } from "./utilities/Icons"
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
import { restrictToVerticalAxis } from "@dnd-kit/modifiers"
import { CSS } from "@dnd-kit/utilities"
import { usePlaybackQueueContext } from "~/contexts/PlaybackQueueContext"
import VCMembersContainer from "./VCMembersContainer"

function DragHandle() {
    return (
        <svg className="w-3 h-4 text-zinc-600 flex-shrink-0" fill="currentColor" viewBox="0 0 8 16">
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
                    <div className="w-10 h-10 rounded bg-zinc-700 animate-pulse flex-shrink-0" />
                    <div className="flex-1 min-w-0 flex flex-col gap-1.5">
                        <div className="h-3 bg-zinc-700 animate-pulse rounded w-3/4" />
                        <div className="h-2.5 bg-zinc-800 animate-pulse rounded w-1/2" />
                    </div>
                </>
            ) : (
                <>
                    <div className="relative w-10 h-10 flex-shrink-0">
                        <img
                            src={item.video.thumbnail ?? ""}
                            alt={item.video.title}
                            className="w-10 h-10 rounded object-cover"
                        />
                        <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 flex items-center justify-center rounded transition">
                            <PlayIcon />
                        </div>
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
                        <div className="skeleton w-10 h-10 rounded flex-shrink-0" />

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
                            className="w-10 h-10 rounded object-cover flex-shrink-0"
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
                                <NextIcon/> :
                                <StopIcon />
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
    const { queue, queuePlayFrom, queueRemove, queueSwap } = usePlaybackQueueContext();

    const sensors = useSensors(useSensor(PointerSensor, {
        activationConstraint: { distance: 5 } // prevents accidental drags on click
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
        <div className="w-112 bg-zinc-900 h-full flex flex-col border-l border-zinc-700 rounded-lg ml-2">
            <VCMembersContainer/>
            <CurrentSong />

            <div className="p-4 border-b border-zinc-700 flex items-center justify-between">
                <p className="font-bold text-white">Queue</p>
                <span className="badge badge-neutral">{queue.length}</span>
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
                        modifiers={[restrictToVerticalAxis]}>
                    <SortableContext items={queue.map(q => q.id)} strategy={verticalListSortingStrategy}>
                        <ul className="flex-1 overflow-y-auto divide-y divide-zinc-800">
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

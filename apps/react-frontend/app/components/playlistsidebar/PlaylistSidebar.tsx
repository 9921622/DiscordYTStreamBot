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
} from "@dnd-kit/sortable"
import { restrictToVerticalAxis, restrictToFirstScrollableAncestor } from "@dnd-kit/modifiers"

import { ListX, Shuffle } from "lucide-react"

import { usePlaylistContext } from "~/contexts/PlaylistContext"
import VCMembersContainer from "../VCMembersContainer"
import PlaylistSidebarSortableItem from "./PlaylistSidebarSortableItem"
import PlaylistSidebarCurrentSong from "./PlaylistSidebarCurrentSong"




function PlaylistHeader({ count, onClear }: { count: number; onClear: () => void }) {
    return (
        <div className="p-4 border-b border-zinc-700 flex items-center justify-between">
            <div className="flex items-center gap-2">
                <p className="font-bold text-white">Queue</p>
                <span className="badge badge-neutral">{count}</span>
            </div>
            <div className="flex items-center gap-1">
                <button title="Shuffle" className="btn btn-ghost btn-xs btn-circle hover:bg-zinc-700" onClick={() => {}}>
                    <Shuffle className="w-6 h-6 text-white" />
                </button>
                <button title="Clear Queue" className="btn btn-ghost btn-xs btn-circle hover:bg-red-500/20 hover:text-red-400" onClick={onClear}>
                    <ListX className="w-6 h-6 text-red-400" />
                </button>
            </div>
        </div>
    )
}

function PlaylistItems() {
    const { queue, remove, reorder, playNow } = usePlaylistContext()

    const sensors = useSensors(useSensor(PointerSensor, {
        activationConstraint: { distance: 5 },
    }))
    function handleDragEnd({ active, over }: DragEndEvent) {
        if (!over || active.id === over.id) return
        const fromIndex = queue.findIndex(q => q.id === active.id)
        const toIndex   = queue.findIndex(q => q.id === over.id)
        if (fromIndex !== -1 && toIndex !== -1) reorder(fromIndex, toIndex)
    }

    return (
        <DndContext
            sensors={sensors}
            collisionDetection={closestCenter}
            onDragEnd={handleDragEnd}
            modifiers={[restrictToVerticalAxis, restrictToFirstScrollableAncestor]}>

            <SortableContext items={queue.map(q => q.id)} strategy={verticalListSortingStrategy}>
                <ul className="flex-1 overflow-y-auto divide-y divide-zinc-800 pb-[var(--musicbar-height,80px)]">
                    {queue.map((item, index) => (
                        <PlaylistSidebarSortableItem
                            key={item.id}
                            item={item}
                            index={index}
                            onPlay={() => { if (!("isSkeleton" in item)) playNow(item) }}
                            onRemove={e => { e.stopPropagation(); remove(index) }}
                        />
                    ))}
                </ul>
            </SortableContext>
        </DndContext>
    );
}



export default function PlaylistSidebar() {
    const { queue, clear } = usePlaylistContext()

    return (
        <div className="w-112 h-full flex flex-col rounded-lg ml-2">
            <VCMembersContainer />
            <PlaylistSidebarCurrentSong />

            <PlaylistHeader count={queue.length} onClear={clear} />

            {queue.length === 0 ? (
                <div className="flex-1 flex items-center justify-center text-zinc-500 text-sm">
                    Queue is empty
                </div>
            ) : (
                <PlaylistItems />
            )}
        </div>
    )
}

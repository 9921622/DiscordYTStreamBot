import { Play, Pause, SkipForward, Square } from "lucide-react"
import { usePlaylistContext } from "~/contexts/PlaylistContext"
import { useCurrentPlayback } from "~/hooks/useCurrentPlayback"
import { EqualizerBars } from "../utilities/Icons"
import MemberAvatar from "../MemberAvatar"
import type { YoutubeVideo } from "~/api/youtube/youtube-types"
import type { DiscordGuildPlaylistItem, DiscordUser } from "~/api/backend-types"

function LoadingSkeleton() {
    return (
        <>
            <div className="skeleton w-30 h-30 rounded flex-shrink-0" />
            <div className="flex-1 min-w-0 space-y-1">
                <div className="skeleton h-3 w-3/4" />
                <div className="skeleton h-3 w-1/2" />
            </div>
            <EqualizerBars className="opacity-50" />
        </>
    )
}

function ResumePrompt({ item, onResume }: { item: DiscordGuildPlaylistItem; onResume: (item: DiscordGuildPlaylistItem) => void }) {
    const video = item.video
    return (
        <>
            <img
                src={video.thumbnail ?? ""}
                alt={video.title}
                className="w-30 h-30 rounded object-cover flex-shrink-0 opacity-50"
            />
            <div className="flex-1 min-w-0">
                <p className="text-zinc-400 text-xs mb-0.5">Continue where you left off</p>
                <p className="text-white text-sm truncate">{video.title}</p>
                <p className="text-zinc-400 text-xs truncate">{video.creator}</p>
            </div>
            <button onClick={() => onResume(item)} className="btn btn-xs btn-ghost text-green-400 hover:bg-green-500/20" title="Resume">
                <Play className="w-5 h-5" />
            </button>
        </>
    )
}

function NowPlaying({ video, addedBy, isPaused, hasQueue, onSkip }: {
    video: YoutubeVideo
    addedBy: DiscordUser | null
    isPaused: boolean
    hasQueue: boolean
    onSkip: () => void
}) {
    return (
        <>
            <div className="relative flex-shrink-0">
                <img
                    src={video.thumbnail ?? ""}
                    alt={video.title}
                    className={`w-30 h-30 rounded object-cover transition ${isPaused ? "opacity-50" : ""}`}
                />
                {addedBy && (
                    <div className="absolute -top-2 -left-2">
                        <MemberAvatar
                            src={addedBy.avatar_url}
                            alt={addedBy.global_name}
                            tooltip={addedBy.global_name}
                            size={20}
                            className="ring-1 ring-zinc-900"
                        />
                    </div>
                )}
            </div>

            <div className="flex-1 min-w-0">
                <p className="text-white text-sm truncate">{video.title}</p>
                <p className="text-zinc-400 text-xs truncate">{video.creator}</p>
            </div>

            {isPaused
                ? <Pause className="w-4 h-4 text-zinc-500 shrink-0" />
                : <EqualizerBars />
            }

            <button
                onClick={onSkip}
                className="btn btn-xs btn-ghost hover:bg-red-500/20"
                title={hasQueue ? "Skip" : "Stop"}
            >
                {hasQueue
                    ? <SkipForward className="w-6 h-6 text-white" />
                    : <Square className="w-6 h-6 text-white" />
                }
            </button>
        </>
    )
}

export default function PlaylistSidebarCurrentSong() {
    const { next, queue, playNow } = usePlaylistContext()
    const { currentItem, currentAddedBy, isLoading, isPlaying, isPaused, isBotOutOfSync } = useCurrentPlayback()

    return (
        <div className="p-3 border-b border-zinc-800">
            <p className="text-xs text-zinc-400 mb-2">Now Playing</p>
            <div className="flex items-center gap-3 bg-zinc-800/60 rounded-md p-2">
                {isBotOutOfSync ? (
                    <ResumePrompt item={currentItem!} onResume={playNow} />
                ) : isLoading ? (
                    <LoadingSkeleton />
                ) : isPlaying || isPaused ? (
                    <NowPlaying
                        video={currentItem?.video!}
                        addedBy={currentAddedBy}
                        isPaused={isPaused}
                        hasQueue={queue.length > 0}
                        onSkip={next}
                    />
                ) : (
                    <p className="text-zinc-500 text-sm">Nothing playing</p>
                )}
            </div>
        </div>
    )
}

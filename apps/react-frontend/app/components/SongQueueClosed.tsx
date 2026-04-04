import { usePlaybackQueueContext } from "~/contexts/PlaybackQueueContext";
import VCMembersContainer from "./VCMembersContainer";
import { usePlaybackVideoContext } from "~/contexts/PlaybackVideoContext";

export default function SongQueueClosed() {
    const { video, videoLoading } = usePlaybackVideoContext();
    const { queue, queuePlayFrom } = usePlaybackQueueContext();

    return (
        <div className="w-full h-full overflow-y-auto flex flex-col items-center gap-2 py-2 px-1.5">
            <VCMembersContainer />

            {/* Divider */}
            <div className="w-full h-px bg-zinc-800" />

            {/* Now Playing */}
            <div className="flex flex-col items-center gap-1.5 w-full">
                <span className="text-[8px] font-bold tracking-[0.2em] text-zinc-500 uppercase">Now playing</span>

                <div className={`relative ${videoLoading ? "opacity-40" : ""}`}>
                    {videoLoading || !video ? (
                        <div className="w-30 h-30 rounded-lg bg-zinc-800 animate-pulse" />
                    ) : (
                        <div className="relative w-30 h-30">
                            <img
                                src={video.thumbnail ?? ""}
                                alt={video.title}
                                title={video.title}
                                className="w-30 h-30 rounded-lg object-cover ring-1 ring-green-500/50"
                            />
                            {/* Animated EQ bars */}
                            <div className="absolute bottom-1 left-0 right-0 flex justify-center gap-[2px] items-end h-3 pointer-events-none">
                                <span className="w-[2px] rounded-full bg-green-400 animate-eq-fast opacity-80" />
                                <span className="w-[2px] rounded-full bg-green-400 animate-eq opacity-80 [animation-delay:-0.2s]" />
                                <span className="w-[2px] rounded-full bg-green-400 animate-eq-slow opacity-80 [animation-delay:-0.4s]" />
                            </div>
                        </div>
                    )}
                </div>

                {/* Title peek — single line, fades out */}
                {video && !videoLoading && (
                    <p className="text-[9px] text-zinc-400 w-full text-center truncate px-1 leading-tight">
                        {video.title}
                    </p>
                )}
            </div>

            {/* Up next divider */}
            {queue.length > 0 && (
                <>
                    <div className="flex flex-col items-center gap-0.5">
                        <div className="w-4 h-px bg-zinc-700" />
                        <span className="text-[8px] tracking-[0.15em] text-zinc-600 uppercase font-bold">Next</span>
                        <div className="w-4 h-px bg-zinc-700" />
                    </div>

                    {/* Queue items */}
                    <ul className="flex flex-col items-center gap-1.5 w-full pb-2">
                        {queue.map((item, index) => {
                            const isSkeleton = "isSkeleton" in item;
                            return (
                                <li
                                    key={item.id}
                                    onClick={() => !isSkeleton && queuePlayFrom(index)}
                                    className={`relative group w-full flex justify-center ${
                                        isSkeleton ? "opacity-40 cursor-wait" : "cursor-pointer"
                                    }`}
                                    title={!isSkeleton ? item.video.title : undefined}
                                >
                                    {isSkeleton ? (
                                        <div className="w-20 h-20 rounded-md bg-zinc-800 animate-pulse" />
                                    ) : (
                                        <div className="relative w-20 h-20">
                                            <img
                                                src={item.video.thumbnail ?? ""}
                                                alt={item.video.title}
                                                className="w-20 h-20 rounded-md object-cover transition-all duration-200 group-hover:brightness-50 group-hover:scale-95"
                                            />
                                            {/* Play icon */}
                                            <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                                                <svg className="w-3.5 h-3.5 text-white" fill="currentColor" viewBox="0 0 16 16">
                                                    <path d="M5 3.5l8 4.5-8 4.5V3.5z" />
                                                </svg>
                                            </div>
                                            {/* Position badge */}
                                            <span className="absolute -top-1 -right-1 text-[7px] bg-zinc-900 text-zinc-500 rounded-full w-3.5 h-3.5 flex items-center justify-center border border-zinc-700 leading-none font-medium">
                                                {index + 1}
                                            </span>
                                        </div>
                                    )}
                                </li>
                            );
                        })}
                    </ul>
                </>
            )}
        </div>
    );
}

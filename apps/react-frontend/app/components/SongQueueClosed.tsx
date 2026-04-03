import { usePlaybackQueueContext } from "~/contexts/PlaybackQueueContext";
import VCMembersContainer from "./VCMembersContainer";
import { usePlaybackVideoContext } from "~/contexts/PlaybackVideoContext";

export default function SongQueueClosed() {
    const { video, videoLoading } = usePlaybackVideoContext();
    const { queue, queuePlayFrom } = usePlaybackQueueContext();

    return (
        <div className="w-full h-full overflow-y-auto flex flex-col rounded-lg ml-2">
            <VCMembersContainer />

            {/* Now Playing */}
            <div className="flex flex-col items-center px-2 pt-3 pb-2 gap-1.5">
                <span className="text-[9px] font-semibold tracking-widest text-zinc-500 uppercase">Now</span>
                <div className={`relative group ${videoLoading ? 'opacity-50' : 'cursor-pointer'}`}>
                    {videoLoading || !video ? (
                        <div className="skeleton w-30 h-30 rounded-md bg-zinc-700" />
                    ) : (
                        <>
                            <img
                                src={video.thumbnail ?? ""}
                                alt={video.title}
                                title={video.title}
                                className="w-30 h-30 rounded-md object-cover ring-2 ring-green-500/60"
                            />
                            {/* Animated eq bars overlay */}
                            <div className="absolute bottom-1 left-0 right-0 flex justify-center gap-[2px] items-end h-3">
                                <span className="w-[2px] bg-green-400 animate-eq-fast opacity-90" />
                                <span className="w-[2px] bg-green-400 animate-eq opacity-90 [animation-delay:-0.2s]" />
                                <span className="w-[2px] bg-green-400 animate-eq-slow opacity-90 [animation-delay:-0.4s]" />
                            </div>
                        </>
                    )}
                </div>
            </div>

            <div className="flex items-center gap-1 px-2 py-1.5">
                <div className="flex-1 h-px bg-zinc-700" />
                <span className="text-[9px] tracking-widest text-zinc-600 uppercase font-semibold">Up next</span>
                <div className="flex-1 h-px bg-zinc-700" />
            </div>

            <ul className="flex flex-col items-center gap-1.5 px-2 pb-2">
                {queue.map((item, index) => {
                    const isSkeleton = 'isSkeleton' in item;
                    return (
                        <li
                            key={item.id}
                            onClick={() => !isSkeleton && queuePlayFrom(index)}
                            className={`relative group ${isSkeleton ? 'opacity-50 cursor-wait' : 'cursor-pointer'}`}
                        >
                            {isSkeleton ? (
                                <div className="w-20 h-20 rounded-md bg-zinc-700 animate-pulse" />
                            ) : (
                                <>
                                    <img
                                        src={item.video.thumbnail ?? ""}
                                        alt={item.video.title}
                                        title={item.video.title}
                                        className="w-20 h-20 rounded-md object-cover transition group-hover:brightness-75"
                                    />
                                    {/* Play icon on hover */}
                                    <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition">
                                        <svg className="w-4 h-4 text-white drop-shadow" fill="currentColor" viewBox="0 0 16 16">
                                            <path d="M5 3.5l8 4.5-8 4.5V3.5z"/>
                                        </svg>
                                    </div>
                                    {/* Index badge */}
                                    <span className="absolute -top-1 -right-1 text-[8px] bg-zinc-800 text-zinc-400 rounded-full w-3.5 h-3.5 flex items-center justify-center leading-none border border-zinc-700">
                                        {index + 1}
                                    </span>
                                </>
                            )}
                        </li>
                    );
                })}
            </ul>
        </div>
    );
}

import { usePlaybackStatusContext } from "~/contexts/PlaybackStatusContext";
import { PlayPauseIcon } from "../utilities/Icons";
import { usePlaylistContext } from "~/contexts/PlaylistContext";
import { Repeat, Shuffle, SkipBack, SkipForward } from "lucide-react";

export default function SongControls({ className }: { className?: string }) {
    const { paused, loop, videoPause, videoLoop } = usePlaybackStatusContext()
    const { queue, next, prev } = usePlaylistContext()

    const isPaused = paused;
    const isLoop   = loop;
    const hasQueue = (queue?.length || 0) > 0;

    const baseBtn = `
        flex items-center justify-center w-8 h-8 rounded-full
        transition-all duration-150 cursor-pointer border-none outline-none bg-transparent
    `
    const secondaryBtn = `${baseBtn} text-white/40 hover:text-white hover:bg-white/10`
    const primaryBtn = `
        flex items-center justify-center w-9 h-9 rounded-full
        bg-white/90 hover:bg-white text-[#111]
        transition-all duration-150 cursor-pointer border-none outline-none
    `
    const dimBtn = `${baseBtn} text-white/20 cursor-default pointer-events-none`

    const onShuffle = () => {}

    return (
        <div className={`${className} flex items-center gap-1.5`}>
            {/* Shuffle */}
            <button className={secondaryBtn} onClick={onShuffle} title="Shuffle">
                <Shuffle className="w-[15px] h-[15px]" />
            </button>

            {/* Previous  */}
            <button className={hasQueue ? secondaryBtn : dimBtn}
                    onClick={hasQueue ? prev : undefined}
                    title="Previous">
                <SkipBack className="w-[17px] h-[17px]" />
            </button>

            {/* Play / Pause — primary */}
            <button className={primaryBtn} onClick={videoPause} title="Play / Pause">
                <PlayPauseIcon isPlaying={!isPaused} className="w-[17px] h-[17px]" />
            </button>

            {/* Next */}
            <button
                className={hasQueue ? secondaryBtn : dimBtn}
                onClick={hasQueue ? next : undefined}
                title="Next"
            >
                <SkipForward className="w-[17px] h-[17px]" />
            </button>

            {/* Loop */}
            <button
                className={`${baseBtn} transition-all duration-150 hover:bg-white/10 ${isLoop ? "text-white" : "text-white/30"}`}
                onClick={videoLoop}
                title="Repeat"
            >
                <div className="relative">
                    <Repeat className="w-[15px] h-[15px]" />
                    {!isLoop && (
                        <span className="absolute inset-0 flex items-center justify-center pointer-events-none">
                            <span className="w-4 h-[1.5px] bg-current rotate-45 rounded-full" />
                        </span>
                    )}
                </div>
            </button>
        </div>
    );
}


import { usePlaybackVideoContext } from "~/contexts/PlaybackVideoContext";
import { PlayPauseIcon } from "../utilities/Icons";
import { usePlaybackQueueContext } from "~/contexts/PlaybackQueueContext";
import { useSocketContext } from "~/contexts/SocketContext";
import { Repeat, Shuffle, SkipBack, SkipForward } from "lucide-react";


const iconClass = "w-6 h-6 text-white";

export default function SongControls({ className }: { className : string }) {
    const { send } = useSocketContext();
    const { videoPlaybackStatus, videoPause } = usePlaybackVideoContext()
    const { queue, queueNext } = usePlaybackQueueContext()

    const isPlaying = videoPlaybackStatus?.playing ?? false;
    const isPaused  = videoPlaybackStatus?.paused ?? false;
    const isLoop    = videoPlaybackStatus?.loop   ?? false;
    const hasQueue  = (queue?.length || 0) > 0;

    const handleLoop = () => {
        send({ type: "loop" })
    }

    const onShuffle = () => {}
    const onPrev = () => {}

    return (
        <div className={`${className} flex items-center gap-4`}>
            <button className="btn btn-ghost btn-circle hover:bg-gray-800" onClick={onShuffle}>
                <Shuffle className={iconClass} />
            </button>
            <button className="pointer-events-none opacity-40 btn btn-ghost btn-circle hover:bg-gray-800" onClick={onPrev}>
                <SkipBack className={iconClass} />
            </button>
            <button className="btn btn-ghost btn-circle hover:bg-gray-800" onClick={videoPause}>
                <PlayPauseIcon isPlaying={!isPaused} className={iconClass} />
            </button>

            <button
                className={`${!hasQueue ? "pointer-events-none opacity-40" : "hover:bg-gray-800"} btn btn-ghost btn-circle hover:bg-gray-800 group relative`}
                onClick={hasQueue ? queueNext : undefined}
                >

                <div className={!hasQueue ? "opacity-40 group-hover:opacity-0 transition-opacity" : ""}>
                    <SkipForward className={iconClass} />
                </div>
            </button>

            <button className="btn btn-ghost btn-circle hover:bg-gray-800" onClick={handleLoop}>
                <div className="relative">
                    <Repeat className={iconClass} />
                    {!isLoop && (
                        <span className="absolute inset-0 flex items-center justify-center pointer-events-none">
                            <span className="w-5 h-[2px] bg-current rotate-45 rounded" />
                        </span>
                    )}
                </div>
            </button>
        </div>
    );
}
